#!/usr/bin/env python3
"Offline user-supplied NSE cash-market EOD CSV/ZIP importer."
import argparse, csv, datetime as dt, io, json, sqlite3, zipfile
from pathlib import Path
FIELDS={'date':['TradDt','DATE1','DATE'],'symbol':['TckrSymb','SYMBOL'],'series':['SctySrs','SERIES'],'open':['OpnPric','OPEN_PRICE','OPEN'],'high':['HghPric','HIGH_PRICE','HIGH'],'low':['LwPric','LOW_PRICE','LOW'],'close':['ClsPric','CLOSE_PRICE','CLOSE'],'prevClose':['PrvsClsgPric','PREV_CLOSE','PREVCLOSE'],'volume':['TtlTradgVol','TTL_TRD_QNTY','TOTTRDQTY']}
def parse_date(s):
 for pattern in ('%Y-%m-%d','%d-%b-%Y','%d/%m/%Y','%d-%m-%Y','%d-%b-%y'):
  try:return dt.datetime.strptime(s.strip(),pattern).date().isoformat()
  except ValueError:pass
 raise ValueError('Unknown date: '+repr(s))
def num(s):
 s=str(s).strip().replace(',','')
 return None if s in ('','-','NA','null') else float(s)
def read_csv(path):
 if path.suffix.lower()=='.zip':
  with zipfile.ZipFile(path) as z:
   candidates=[x for x in z.namelist() if x.lower().endswith('.csv') and not x.startswith('__MACOSX/')]
   if len(candidates)!=1:raise ValueError('ZIP needs exactly one CSV: '+str(candidates))
   return io.StringIO(z.read(candidates[0]).decode('utf-8-sig'))
 return io.StringIO(path.read_text(encoding='utf-8-sig'))
def normalize(row):
 cols={str(k).strip().lower():v for k,v in row.items() if k is not None}
 def get(k,required=True):
  for alt in FIELDS[k]:
   if alt.lower() in cols:return (cols[alt.lower()] or '').strip()
  if required:raise ValueError('Missing '+k+'; available: '+str(sorted(cols)))
  return ''
 d=parse_date(get('date'));sym=get('symbol');series=get('series');v={k:num(get(k)) for k in ('open','high','low','close','volume')}
 if not sym or not series or any(x is None or x<0 for x in v.values()):raise ValueError('Missing symbol/series or invalid OHLCV')
 if v['high']<max(v['open'],v['close']) or v['low']>min(v['open'],v['close']):raise ValueError('Inconsistent OHLC: '+sym+' '+d)
 prev=num(get('prevClose',False))
 if prev is not None and prev<0:raise ValueError('Negative previous close')
 if not v['volume'].is_integer():raise ValueError('Noninteger volume')
 return(d,sym,series,v['open'],v['high'],v['low'],v['close'],prev,int(v['volume']))
def connect(path):
 con=sqlite3.connect(path)
 con.executescript("""CREATE TABLE IF NOT EXISTS prices(date TEXT NOT NULL,symbol TEXT NOT NULL,series TEXT NOT NULL,open REAL NOT NULL,high REAL NOT NULL,low REAL NOT NULL,close REAL NOT NULL,prevClose REAL,volume INTEGER NOT NULL,PRIMARY KEY(date,symbol,series));
 CREATE TABLE IF NOT EXISTS flags(date TEXT NOT NULL,symbol TEXT NOT NULL,series TEXT NOT NULL,PRIMARY KEY(date,symbol,series));
 CREATE INDEX IF NOT EXISTS idx_chart ON prices(symbol,series,date);
 CREATE INDEX IF NOT EXISTS idx_flags_date ON flags(date);""")
 return con
def subtract_years(s,n):
 d=dt.date.fromisoformat(s)
 try:return d.replace(year=d.year-n).isoformat()
 except ValueError:return d.replace(year=d.year-n,day=28).isoformat()
def refresh(con):
 newest=con.execute('SELECT MAX(date) FROM prices').fetchone()[0]
 if not newest:return None
 con.execute('DELETE FROM prices WHERE date < ?',(subtract_years(newest,5),))
 con.execute('DELETE FROM flags')
 con.execute("""INSERT INTO flags(date,symbol,series) SELECT date,symbol,series FROM prices
 WHERE series='EQ' AND date>=? AND CAST(ROUND(close*100) AS INTEGER)=CAST(ROUND(high*100) AS INTEGER)""",(subtract_years(newest,1),))
 return newest
def import_file(con,path):
 reader=csv.DictReader(read_csv(path));count=0
 with con:
  for line,row in enumerate(reader,2):
   if not any(str(v or '').strip() for v in row.values()):continue
   try:item=normalize(row)
   except Exception as e:raise ValueError(f'{path.name} line {line}: {e}') from e
   con.execute('INSERT OR REPLACE INTO prices(date,symbol,series,open,high,low,close,prevClose,volume) VALUES (?,?,?,?,?,?,?,?,?)',item)
   count+=1
  newest=refresh(con)
 return count,newest
def export(con,path,symbols):
 newest=con.execute('SELECT MAX(date) FROM prices').fetchone()[0]
 if newest is None:raise ValueError('Database empty')
 symbols=[x.strip() for x in symbols.split(',') if x.strip()]
 if not symbols or len(symbols)>35:raise ValueError('Pilot requires --symbols with 1–35 EQ symbols')
 q=','.join('?' for _ in symbols)
 cur=con.execute(f"SELECT date,symbol,series,open,high,low,close,prevClose,volume FROM prices WHERE (series='EQ' AND symbol IN ({q})) OR (series!='EQ' AND date=?) ORDER BY date,symbol,series",(*symbols,newest))
 names=[x[0] for x in cur.description];rows=[dict(zip(names,r)) for r in cur]
 if len(rows)>150000:raise ValueError('Pilot exceeds 150,000 rows; choose fewer EQ symbols')
 payload={'meta':{'type':'nse-eod-pilot-export-v1','latestDate':newest,'eqSymbols':symbols,'scope':'selected EQ five years + latest non-EQ','note':'User-provided source files only'},'rows':rows}
 path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(payload,separators=(',',':')),encoding='utf-8');return len(rows)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--db',default='market.db');p.add_argument('--import-file',type=Path,action='append',default=[]);p.add_argument('--export',type=Path);p.add_argument('--symbols',default='');a=p.parse_args()
 with connect(a.db) as con:
  for path in a.import_file:
   n,date=import_file(con,path);print(f'Imported {n} rows from {path}; latest dataset date {date}')
  if a.export:print('Exported',export(con,a.export,a.symbols),'rows to',a.export)
  print('Stored EQ flags:',con.execute('SELECT COUNT(*) FROM flags').fetchone()[0])
if __name__=='__main__':main()
