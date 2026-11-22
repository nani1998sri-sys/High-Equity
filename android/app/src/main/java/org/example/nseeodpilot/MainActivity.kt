package org.example.nseeodpilot

import android.app.Activity
import android.content.Intent
import android.os.Bundle
import android.webkit.JavascriptInterface
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.net.URLEncoder
import java.io.ByteArrayOutputStream
import java.io.File
import kotlin.concurrent.thread
import android.webkit.ValueCallback
import android.webkit.WebChromeClient
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.webkit.WebViewAssetLoader

/** Pilot: bundled UI; only user-configured public GitHub JSON snapshots are fetched. */
class MainActivity : Activity() {
    private var fileCallback: ValueCallback<Array<android.net.Uri>>? = null
    private val requestCode = 4321
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val loader = WebViewAssetLoader.Builder()
            .addPathHandler("/assets/", WebViewAssetLoader.AssetsPathHandler(this)).build()
        val view = WebView(this)
        view.settings.javaScriptEnabled = true
        view.settings.domStorageEnabled = true
        view.settings.allowFileAccess = false
        view.settings.allowContentAccess = true
        view.settings.mixedContentMode = WebSettings.MIXED_CONTENT_NEVER_ALLOW
        view.addJavascriptInterface(object {
            @JavascriptInterface
            fun saveSnapshot(json: String): Boolean = try {
                if (json.toByteArray(Charsets.UTF_8).size > 18_000_000) false else {
                    val temp = File(filesDir, "market-snapshot.tmp")
                    val target = File(filesDir, "market-snapshot.json")
                    temp.writeText(json, Charsets.UTF_8)
                    if (temp.renameTo(target)) true else {
                        target.writeText(json, Charsets.UTF_8)
                        temp.delete()
                        true
                    }
                }
            } catch (_: Exception) { false }
            @JavascriptInterface
            fun loadSnapshot(): String = try {
                val file = File(filesDir, "market-snapshot.json")
                if (file.exists() && file.length() <= 18_000_000) file.readText(Charsets.UTF_8) else ""
            } catch (_: Exception) { "" }
            @JavascriptInterface
            fun clearSnapshot() {
                File(filesDir, "market-snapshot.json").delete()
            }
            @JavascriptInterface
            fun refresh(owner: String, repo: String, branch: String, path: String) {
                // Trust neither JS inputs nor remote repository contents: fixed HTTPS host, path-only components.
                val ownerOk = owner.matches(Regex("[A-Za-z0-9][A-Za-z0-9-]{0,38}"))
                val repoOk = repo.matches(Regex("[A-Za-z0-9_.-]{1,100}")) && !repo.startsWith(".")
                val branchOk = branch.matches(Regex("[A-Za-z0-9][A-Za-z0-9._-]{0,99}")) && !branch.contains("..")
                val pathOk = path.matches(Regex("[A-Za-z0-9_.-]+(/[A-Za-z0-9_.-]+)*\\.json", RegexOption.IGNORE_CASE)) && !path.contains("..")
                if (!ownerOk || !repoOk || !branchOk || !pathOk) {
                    runOnUiThread { view.evaluateJavascript("window.nseNativeResponse(null, 'Invalid GitHub source')", null) }
                    return
                }
                thread(name = "nse-github-refresh") {
                    try {
                        val segments = listOf(owner, repo, branch) + path.split('/')
                        val uri = "https://raw.githubusercontent.com/" + segments.joinToString("/") {
                            URLEncoder.encode(it, "UTF-8").replace("+", "%20")
                        }
                        val connection = URL(uri).openConnection() as HttpURLConnection
                        connection.connectTimeout = 10000
                        connection.readTimeout = 15000
                        connection.instanceFollowRedirects = false
                        connection.setRequestProperty("Accept", "application/json")
                        connection.setRequestProperty("Cache-Control", "no-cache")
                        try {
                            if (connection.responseCode != 200) throw IllegalStateException("GitHub HTTP ${connection.responseCode}")
                            val out = ByteArrayOutputStream()
                            connection.inputStream.use { input ->
                                val buffer = ByteArray(8192)
                                while (true) {
                                    val n = input.read(buffer)
                                    if (n < 0) break
                                    if (out.size() + n > 18_000_000) throw IllegalStateException("Snapshot exceeds 18 MB")
                                    out.write(buffer, 0, n)
                                }
                            }
                            val json = out.toString("UTF-8")
                            // JSONObject.quote ensures remote JSON is data, never executable JavaScript.
                            runOnUiThread { view.evaluateJavascript("window.nseNativeResponse(${JSONObject.quote(json)}, null)", null) }
                        } finally { connection.disconnect() }
                    } catch (ex: Exception) {
                        val message = JSONObject.quote(ex.message?.take(180) ?: "Network error")
                        runOnUiThread { view.evaluateJavascript("window.nseNativeResponse(null, $message)", null) }
                    }
                }
            }
        }, "NseBridge")
        view.webViewClient = object : WebViewClient() {
            override fun shouldInterceptRequest(view: WebView?, request: WebResourceRequest): WebResourceResponse? =
                loader.shouldInterceptRequest(request.url)
            override fun shouldOverrideUrlLoading(view: WebView?, request: WebResourceRequest): Boolean =
                request.url.host != "appassets.androidplatform.net"
        }
        view.webChromeClient = object : WebChromeClient() {
            override fun onShowFileChooser(webView: WebView?, callback: ValueCallback<Array<android.net.Uri>>?, params: FileChooserParams?): Boolean {
                fileCallback?.onReceiveValue(null)
                fileCallback = callback
                return try {
                    val intent = Intent(Intent.ACTION_GET_CONTENT).apply {
                        type = "application/json"
                        addCategory(Intent.CATEGORY_OPENABLE)
                    }
                    startActivityForResult(Intent.createChooser(intent, "Choose NSE pilot JSON"), requestCode)
                    true
                } catch (ex: Exception) {
                    fileCallback = null
                    callback?.onReceiveValue(null)
                    false
                }
            }
        }
        setContentView(view)
        view.loadUrl("https://appassets.androidplatform.net/assets/index.html")
    }
    @Deprecated("File chooser compatibility on API 26+")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == this.requestCode) {
            fileCallback?.onReceiveValue(if (resultCode == RESULT_OK && data?.data != null) arrayOf(data.data!!) else null)
            fileCallback = null
        }
    }
    override fun onDestroy() {
        (findViewById<android.view.View>(android.R.id.content) as? android.view.ViewGroup)?.let { parent ->
            for (i in 0 until parent.childCount) (parent.getChildAt(i) as? WebView)?.destroy()
        }
        super.onDestroy()
    }
}
