import io,json,sqlite3,tempfile,unittest,zipfile
from pathlib import Path
from pipeline.ingest import connect, import_file, export
class PipelineTest(unittest.TestCase):
 def test_ingest_flags_idempotence_export_and_retention(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);db=connect(root/'test.db')
   old=root/'old.csv';old.write_text('DATE1,SYMBOL,SERIES,OPEN_PRICE,HIGH_PRICE,LOW_PRICE,CLOSE_PRICE,PREV_CLOSE,TTL_TRD_QNTY\n18-Nov-2020,TEST,EQ,10,11,9,11,10,100\n18-Nov-2025,TEST,EQ,10,11,9,11,10,120\n')
   imported,latest=import_file(db,old);self.assertEqual(imported,2)
   current=root/'current.zip'
   csvdata='TradDt,TckrSymb,SctySrs,OpnPric,HghPric,LwPric,ClsPric,PrvsClsgPric,TtlTradgVol\n2026-11-20,TEST,EQ,100,105,99,105,100,1500\n2026-11-20,OTHER,BE,200,210,198,208,200,3000\n'
   with zipfile.ZipFile(current,'w') as z:z.writestr('cm_udiff.csv',csvdata)
   self.assertEqual(import_file(db,current)[1],'2026-11-20');import_file(db,current)
   self.assertEqual(db.execute('SELECT COUNT(*) FROM prices').fetchone()[0],3)
   self.assertEqual(db.execute('SELECT COUNT(*) FROM flags').fetchone()[0],1)
   self.assertEqual(db.execute('SELECT date FROM flags').fetchone()[0],'2026-11-20')
   out=root/'export.json';self.assertEqual(export(db,out,'TEST'),3)
   data=json.loads(out.read_text());self.assertEqual(sum(r['series']!='EQ' for r in data['rows']),1)
   self.assertEqual(next(r for r in data['rows'] if r['date']=='2025-11-18')['close'],11)
   db.close()
if __name__=='__main__':unittest.main()
