plugins { id("com.android.application"); id("org.jetbrains.kotlin.android") }
android { namespace = "org.example.nseeodpilot"; compileSdk = 35
 defaultConfig { applicationId = "org.example.nseeodpilot"; minSdk = 26; targetSdk = 35; versionCode = 1; versionName = "0.1-pilot" }
 compileOptions { sourceCompatibility = JavaVersion.VERSION_17; targetCompatibility = JavaVersion.VERSION_17 }
 kotlinOptions { jvmTarget = "17" }
}
dependencies { implementation("androidx.webkit:webkit:1.10.0") }
