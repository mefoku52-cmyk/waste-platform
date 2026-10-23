#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail
umask 077

PROJECT="$HOME/FakeGPSPro"
SDK="${ANDROID_HOME:-$HOME/android-sdk}"
BUILD="$HOME/.cache/fakegps-gradle-8.9"
mkdir -p "$HOME/.cache" "$PROJECT"
export ANDROID_HOME="$SDK"
export ANDROID_SDK_ROOT="$SDK"

for cmd in wget unzip; do
  command -v "$cmd" >/dev/null 2>&1 || {
    echo "CHYBA: Chýba $cmd. Nainštaluj ho príkazom: pkg install $cmd"
    exit 1
  }
done

if [ ! -x "$BUILD/bin/gradle" ]; then
  mkdir -p "$HOME/.cache"
  wget -q --show-progress \
    https://services.gradle.org/distributions/gradle-8.9-bin.zip \
    -O "$HOME/.cache/gradle-8.9-bin.zip"
  unzip -q "$HOME/.cache/gradle-8.9-bin.zip" -d "$HOME/.cache"
fi

G="$BUILD/bin/gradle"
if [ ! -x "$G" ]; then
  echo "CHYBA: Gradle 8.9 sa nepodarilo pripraviť."
  exit 1
fi

mkdir -p "$PROJECT/app/src/main/java/sk/fakegps/pro"
mkdir -p "$PROJECT/app/src/main/res/values"
mkdir -p "$PROJECT/app/src/main/res/drawable"

cd "$PROJECT"

cat > settings.gradle.kts <<'FILE_SETTINGS'
pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}
rootProject.name = "FakeGPSPro"
include(":app")
FILE_SETTINGS

cat > build.gradle.kts <<'FILE_ROOT'
plugins {
    id("com.android.application") version "8.7.3" apply false
    id("org.jetbrains.kotlin.android") version "2.0.21" apply false
    id("com.google.devtools.ksp") version "2.0.21-1.0.28" apply false
}
FILE_ROOT

cat > gradle.properties <<'FILE_PROPERTIES'
org.gradle.jvmargs=-Xmx1536m -XX:MaxMetaspaceSize=512m -Dfile.encoding=UTF-8
org.gradle.parallel=false
android.useAndroidX=true
kotlin.code.style=official
FILE_PROPERTIES

cat > local.properties <<FILE_LOCAL
sdk.dir=$SDK
FILE_LOCAL

cat > app/build.gradle.kts <<'FILE_APP'
plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("com.google.devtools.ksp")
}

android {
    namespace = "sk.fakegps.pro"
    compileSdk = 35

    defaultConfig {
        applicationId = "sk.fakegps.pro"
        minSdk = 26
        targetSdk = 34
        versionCode = 1
        versionName = "1.0"
    }

    buildFeatures {
        compose = true
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }

    packaging {
        resources.excludes += "/META-INF/{AL2.0,LGPL2.1}"
    }
}

dependencies {
    val composeBom = platform("androidx.compose:compose-bom:2024.10.00")
    implementation(composeBom)
    androidTestImplementation(composeBom)

    implementation("androidx.core:core-ktx:1.15.0")
    implementation("androidx.activity:activity-compose:1.9.3")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.8.7")
    implementation("androidx.lifecycle:lifecycle-runtime-compose:2.8.7")
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.compose.foundation:foundation")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.material:material-icons-extended")
    debugImplementation("androidx.compose.ui:ui-tooling")

    implementation("androidx.room:room-runtime:2.6.1")
    implementation("androidx.room:room-ktx:2.6.1")
    ksp("androidx.room:room-compiler:2.6.1")

    implementation("androidx.datastore:datastore-preferences:1.1.1")
    implementation("org.osmdroid:osmdroid-android:6.1.20")
}
FILE_APP

cat > app/src/main/AndroidManifest.xml <<'FILE_MANIFEST'
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
    <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE" />
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE_LOCATION" />
    <uses-permission android:name="android.permission.POST_NOTIFICATIONS" />
    <uses-permission android:name="android.permission.SYSTEM_ALERT_WINDOW" />
    <uses-permission android:name="android.permission.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS" />

    <application
        android:allowBackup="false"
        android:label="FakeGPS Pro"
        android:theme="@style/AppTheme"
        android:usesCleartextTraffic="false">
        <activity
            android:name=".MainActivity"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
        <service
            android:name=".MockLocationService"
            android:exported="false"
            android:foregroundServiceType="location" />
    </application>
</manifest>
FILE_MANIFEST

cat > app/src/main/res/values/styles.xml <<'FILE_STYLE'
<resources>
    <style name="AppTheme" parent="@android:style/Theme.Material.Light.NoActionBar">
        <item name="android:fontFamily">sans</item>
        <item name="android:colorAccent">#1769AA</item>
        <item name="android:windowLightStatusBar">true</item>
        <item name="android:statusBarColor">#F3F5F9</item>
        <item name="android:navigationBarColor">#F3F5F9</item>
    </style>
</resources>
FILE_STYLE

cat > app/src/main/java/sk/fakegps/pro/PlaceDatabase.kt <<'FILE_DB'
package sk.fakegps.pro

import android.content.Context
import androidx.room.Dao
import androidx.room.Database
import androidx.room.Entity
import androidx.room.Insert
import androidx.room.PrimaryKey
import androidx.room.Query
import androidx.room.Room
import androidx.room.RoomDatabase
import kotlinx.coroutines.flow.Flow

@Entity(tableName = "places")
data class Place(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val name: String,
    val latitude: Double,
    val longitude: Double,
    val note: String = "",
    val createdAt: Long = System.currentTimeMillis()
)

@Dao
interface PlaceDao {
    @Query("SELECT * FROM places ORDER BY createdAt DESC")
    fun observeAll(): Flow<List<Place>>

    @Insert
    suspend fun insert(place: Place)

    @Query("DELETE FROM places WHERE id = :id")
    suspend fun delete(id: Long)
}

@Database(entities = [Place::class], version = 1, exportSchema = false)
abstract class PlaceDatabase : RoomDatabase() {
    abstract fun places(): PlaceDao

    companion object {
        @Volatile private var instance: PlaceDatabase? = null

        fun get(context: Context): PlaceDatabase =
            instance ?: synchronized(this) {
                instance ?: Room.databaseBuilder(
                    context.applicationContext,
                    PlaceDatabase::class.java,
                    "fakegps.db"
                ).build().also { instance = it }
            }
    }
}
FILE_DB

cat > app/src/main/java/sk/fakegps/pro/MockLocationService.kt <<'FILE_SERVICE'
package sk.fakegps.pro

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Intent
import android.location.Location
import android.location.LocationManager
import android.os.Build
import android.os.IBinder
import android.os.SystemClock
import androidx.core.app.NotificationCompat
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.cancel
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import kotlin.math.max

class MockLocationService : Service() {
    private val scope = CoroutineScope(Dispatchers.Default)
    private var job: Job? = null
    private var paused = false
    private var lat = 48.1486
    private var lon = 17.1077
    private var speed = 0.0
    private var jitter = 0.0
    private var altitude = 180.0

    private val channelId = "fakegps_running"

    override fun onCreate() {
        super.onCreate()
        val manager = getSystemService(NotificationManager::class.java)
        manager.createNotificationChannel(
            NotificationChannel(
                channelId,
                "FakeGPS Pro",
                NotificationManager.IMPORTANCE_LOW
            )
        )
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            "STOP" -> {
                stopSimulation()
                stopForeground(STOP_FOREGROUND_REMOVE)
                stopSelf()
                return START_NOT_STICKY
            }
            "PAUSE" -> {
                paused = !paused
                updateNotification()
                return START_STICKY
            }
            else -> {
                lat = intent?.getDoubleExtra("lat", lat) ?: lat
                lon = intent?.getDoubleExtra("lon", lon) ?: lon
                speed = intent?.getDoubleExtra("speed", 0.0) ?: 0.0
                jitter = intent?.getDoubleExtra("jitter", 0.0) ?: 0.0
                altitude = intent?.getDoubleExtra("altitude", 180.0) ?: 180.0
                startForeground(10, notification())
                if (job == null) startSimulation()
            }
        }
        return START_STICKY
    }

    private fun notification(): Notification {
        fun action(label: String, value: String): PendingIntent {
            val i = Intent(this, MockLocationService::class.java).setAction(value)
            return PendingIntent.getService(
                this,
                value.hashCode(),
                i,
                PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
            )
        }

        val open = PendingIntent.getActivity(
            this, 0, Intent(this, MainActivity::class.java),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        return NotificationCompat.Builder(this, channelId)
            .setSmallIcon(android.R.drawable.ic_menu_mylocation)
            .setContentTitle("FakeGPS Pro")
            .setContentText(if (paused) "Simulácia pozastavená" else "Simulácia polohy aktívna")
            .setContentIntent(open)
            .setOngoing(true)
            .addAction(0, if (paused) "Pokračovať" else "Pauza", action("Pauza", "PAUSE"))
            .addAction(0, "Stop", action("Stop", "STOP"))
            .build()
    }

    private fun updateNotification() {
        getSystemService(NotificationManager::class.java).notify(10, notification())
    }

    @Suppress("DEPRECATION")
    private fun startSimulation() {
        val lm = getSystemService(LOCATION_SERVICE) as LocationManager
        val providers = listOf(LocationManager.GPS_PROVIDER, LocationManager.NETWORK_PROVIDER)

        try {
            for (provider in providers) {
                try {
                    lm.addTestProvider(
                        provider, false, false, false, false,
                        true, true, true,
                        android.location.Criteria.POWER_LOW,
                        android.location.Criteria.ACCURACY_FINE
                    )
                } catch (_: IllegalArgumentException) {
                    // Poskytovateľ už existuje; pokúsime sa ho znovu aktivovať.
                }
                lm.setTestProviderEnabled(provider, true)
            }

            job = scope.launch {
                while (isActive) {
                    if (!paused) {
                        val now = SystemClock.elapsedRealtimeNanos()
                        val noiseLat = (Math.random() - 0.5) * jitter / 111_000.0
                        val noiseLon = (Math.random() - 0.5) * jitter /
                            max(1.0, 111_000.0 * kotlin.math.cos(Math.toRadians(lat)))

                        for (provider in providers) {
                            val location = Location(provider).apply {
                                latitude = (lat + noiseLat).coerceIn(-90.0, 90.0)
                                longitude = (lon + noiseLon).coerceIn(-180.0, 180.0)
                                this.altitude = this@MockLocationService.altitude
                                accuracy = (3f + jitter.toFloat()).coerceAtLeast(1f)
                                this.speed = this@MockLocationService.speed.toFloat()
                                bearing = 0f
                                time = System.currentTimeMillis()
                                elapsedRealtimeNanos = now
                            }
                            try {
                                lm.setTestProviderLocation(provider, location)
                            } catch (e: SecurityException) {
                                android.util.Log.e("FakeGPS", "Nie je povolená mock poloha", e)
                                stopSelf()
                                return@launch
                            } catch (e: IllegalArgumentException) {
                                android.util.Log.e("FakeGPS", "Neplatný poskytovateľ", e)
                            }
                        }
                    }
                    delay(1000)
                }
            }
        } catch (e: SecurityException) {
            android.util.Log.e("FakeGPS", "Vyber FakeGPS Pro v nastaveniach vývojára", e)
            stopSelf()
        } catch (e: Exception) {
            android.util.Log.e("FakeGPS", "Spustenie simulácie zlyhalo", e)
            stopSelf()
        }
    }

    @Suppress("DEPRECATION")
    private fun stopSimulation() {
        job?.cancel()
        job = null
        val lm = getSystemService(LOCATION_SERVICE) as LocationManager
        for (provider in listOf(LocationManager.GPS_PROVIDER, LocationManager.NETWORK_PROVIDER)) {
            try {
                lm.setTestProviderEnabled(provider, false)
                lm.removeTestProvider(provider)
            } catch (_: Exception) {
                // Upratovanie poskytovateľa nesmie zhodiť aplikáciu.
            }
        }
    }

    override fun onDestroy() {
        stopSimulation()
        scope.cancel()
        super.onDestroy()
    }

    override fun onBind(intent: Intent?): IBinder? = null
}
FILE_SERVICE

cat > app/src/main/java/sk/fakegps/pro/MainActivity.kt <<'FILE_MAIN'
package sk.fakegps.pro

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.location.Geocoder
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.launch
import org.osmdroid.config.Configuration
import org.osmdroid.tileprovider.tilesource.TileSourceFactory
import org.osmdroid.util.GeoPoint
import org.osmdroid.views.MapView
import org.osmdroid.views.overlay.MapEventsOverlay
import org.osmdroid.events.MapEventsReceiver
import java.util.Locale

class MainActivity : ComponentActivity() {
    private val permissions = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        Configuration.getInstance().userAgentValue = packageName
        Configuration.getInstance().load(
            applicationContext,
            androidx.preference.PreferenceManager.getDefaultSharedPreferences(applicationContext)
        )

        setContent {
            MaterialTheme {
                Surface(Modifier.fillMaxSize()) {
                    FakeGpsScreen()
                }
            }
        }
    }

    @Composable
    private fun FakeGpsScreen() {
        val dao = remember { PlaceDatabase.get(this).places() }
        val places by dao.observeAll().collectAsStateWithLifecycle(initialValue = emptyList())

        var latitude by remember { mutableStateOf("48.1486") }
        var longitude by remember { mutableStateOf("17.1077") }
        var speed by remember { mutableStateOf("0") }
        var jitter by remember { mutableStateOf("0") }
        var altitude by remember { mutableStateOf("180") }
        var name by remember { mutableStateOf("Testovací bod") }
        var address by remember { mutableStateOf("") }
        var status by remember { mutableStateOf("Pripravené") }

        fun parseCoordinates(): Pair<Double, Double>? {
            val lat = latitude.toDoubleOrNull()
            val lon = longitude.toDoubleOrNull()
            if (lat == null || lon == null ||
                !lat.isFinite() || !lon.isFinite() ||
                lat !in -90.0..90.0 || lon !in -180.0..180.0
            ) return null
            return lat to lon
        }

        Column(
            Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            Text("FakeGPS Pro", style = MaterialTheme.typography.headlineMedium)
            Text("Vývojársky nástroj na testovanie simulovanej polohy.")
            Text("Stav: $status")

            Card(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("Súradnice")
                    OutlinedTextField(
                        latitude, { latitude = it }, label = { Text("Zemepisná šírka") },
                        modifier = Modifier.fillMaxWidth(), singleLine = true
                    )
                    OutlinedTextField(
                        longitude, { longitude = it }, label = { Text("Zemepisná dĺžka") },
                        modifier = Modifier.fillMaxWidth(), singleLine = true
                    )
                    OutlinedTextField(
                        altitude, { altitude = it }, label = { Text("Nadmorská výška (m)") },
                        modifier = Modifier.fillMaxWidth(), singleLine = true
                    )
                    OutlinedTextField(
                        speed, { speed = it }, label = { Text("Rýchlosť (km/h)") },
                        modifier = Modifier.fillMaxWidth(), singleLine = true
                    )
                    OutlinedTextField(
                        jitter, { jitter = it }, label = { Text("Jitter (m)") },
                        modifier = Modifier.fillMaxWidth(), singleLine = true
                    )
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        Button(onClick = {
                            val p = parseCoordinates()
                            val s = speed.toDoubleOrNull()
                            val j = jitter.toDoubleOrNull()
                            val a = altitude.toDoubleOrNull()
                            if (p == null || s == null || j == null || a == null ||
                                s < 0 || j < 0 || !s.isFinite() || !j.isFinite() || !a.isFinite()
                            ) {
                                status = "Neplatné hodnoty súradníc alebo parametrov."
                            } else if (ContextCompat.checkSelfPermission(
                                    this@MainActivity, Manifest.permission.ACCESS_FINE_LOCATION
                                ) != PackageManager.PERMISSION_GRANTED
                            ) {
                                permissions.launch(
                                    buildList {
                                        add(Manifest.permission.ACCESS_FINE_LOCATION)
                                        add(Manifest.permission.ACCESS_COARSE_LOCATION)
                                        if (Build.VERSION.SDK_INT >= 33) add(Manifest.permission.POST_NOTIFICATIONS)
                                    }.toTypedArray()
                                )
                                status = "Povoľ polohu a potom spusti simuláciu znova."
                            } else {
                                val i = Intent(this@MainActivity, MockLocationService::class.java).apply {
                                    putExtra("lat", p.first)
                                    putExtra("lon", p.second)
                                    putExtra("speed", s / 3.6)
                                    putExtra("jitter", j)
                                    putExtra("altitude", a)
                                }
                                try {
                                    ContextCompat.startForegroundService(this@MainActivity, i)
                                    status = "Požiadavka na spustenie odoslaná."
                                } catch (e: Exception) {
                                    status = "Chyba: ${e.javaClass.simpleName}: ${e.message}"
                                }
                            }
                        }) { Text("Štart") }

                        OutlinedButton(onClick = {
                            startService(Intent(this@MainActivity, MockLocationService::class.java).setAction("PAUSE"))
                            status = "Požiadavka na pauzu odoslaná."
                        }) { Text("Pauza") }

                        OutlinedButton(onClick = {
                            startService(Intent(this@MainActivity, MockLocationService::class.java).setAction("STOP"))
                            status = "Zastavené."
                        }) { Text("Stop") }
                    }
                    OutlinedButton(onClick = {
                        startActivity(Intent(Settings.ACTION_APPLICATION_DEVELOPMENT_SETTINGS))
                    }) {
                        Text("Nastavenia vývojára")
                    }
                }
            }

            Card(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("Mapa OpenStreetMap")
                    Text("Ťuknutím na mapu vyber bod. Mapové dlaždice vyžadujú internet.")
                    AndroidMap(
                        onPoint = { point ->
                            latitude = point.latitude.toString()
                            longitude = point.longitude.toString()
                        }
                    )
                    OutlinedTextField(
                        address, { address = it },
                        label = { Text("Adresa na vyhľadanie") },
                        modifier = Modifier.fillMaxWidth()
                    )
                    Button(onClick = {
                        lifecycleScope.launch {
                            try {
                                @Suppress("DEPRECATION")
                                val results = Geocoder(this@MainActivity, Locale.getDefault())
                                    .getFromLocationName(address, 1)
                                val result = results?.firstOrNull()
                                if (result != null) {
                                    latitude = result.latitude.toString()
                                    longitude = result.longitude.toString()
                                    status = "Adresa nájdená."
                                } else {
                                    status = "Adresa sa nenašla."
                                }
                            } catch (e: Exception) {
                                status = "Vyhľadávanie zlyhalo: ${e.message}"
                            }
                        }
                    }) { Text("Vyhľadať adresu") }
                }
            }

            Card(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("Obľúbené body a história")
                    OutlinedTextField(
                        name, { name = it }, label = { Text("Názov bodu") },
                        modifier = Modifier.fillMaxWidth()
                    )
                    Button(onClick = {
                        val p = parseCoordinates()
                        if (p == null || name.isBlank()) {
                            status = "Zadaj platné súradnice a názov."
                        } else {
                            lifecycleScope.launch {
                                dao.insert(Place(
                                    name = name.trim(),
                                    latitude = p.first,
                                    longitude = p.second
                                ))
                                status = "Bod uložený."
                            }
                        }
                    }) { Text("Uložiť bod") }

                    LazyColumn(modifier = Modifier.fillMaxWidth().heightIn(max = 300.dp)) {
                        items(places, key = { it.id }) { place ->
                            Row(
                                Modifier.fillMaxWidth().padding(vertical = 4.dp),
                                horizontalArrangement = Arrangement.SpaceBetween
                            ) {
                                Column(Modifier.weight(1f)) {
                                    Text(place.name)
                                    Text("${place.latitude}, ${place.longitude}")
                                }
                                OutlinedButton(onClick = {
                                    latitude = place.latitude.toString()
                                    longitude = place.longitude.toString()
                                    name = place.name
                                }) { Text("Použiť") }
                                OutlinedButton(onClick = {
                                    lifecycleScope.launch { dao.delete(place.id) }
                                }) { Text("Zmazať") }
                            }
                        }
                    }
                }
            }

            Text(
                "Upozornenie: vyber FakeGPS Pro v Možnostiach pre vývojárov. " +
                    "Niektoré aplikácie mock polohu detegujú. Android môže službu na pozadí ukončiť."
            )
        }
    }

    @Composable
    private fun AndroidMap(onPoint: (GeoPoint) -> Unit) {
        val map = remember {
            MapView(this).apply {
                setTileSource(TileSourceFactory.MAPNIK)
                setMultiTouchControls(true)
                controller.setZoom(12.0)
                controller.setCenter(GeoPoint(48.1486, 17.1077))
                overlays.add(MapEventsOverlay(object : MapEventsReceiver {
                    override fun singleTapConfirmedHelper(p: GeoPoint): Boolean {
                        onPoint(p)
                        return true
                    }
                    override fun longPressHelper(p: GeoPoint): Boolean {
                        onPoint(p)
                        return true
                    }
                }))
            }
        }
        androidx.compose.ui.viewinterop.AndroidView(
            factory = { map },
            modifier = Modifier.fillMaxWidth().height(260.dp),
            update = { it.invalidate() }
        )
        DisposableEffect(map) {
            onDispose { map.onDetach() }
        }
    }
}
FILE_MAIN

# osmdroid potrebuje AndroidX Preference pre načítanie konfigurácie.
sed -i '/implementation("androidx.core:core-ktx/a\    implementation("androidx.preference:preference-ktx:1.2.1")' app/build.gradle.kts

echo "=== FakeGPS Pro: BUILD ==="
"$G" --no-daemon --stacktrace assembleDebug

APK="$PROJECT/app/build/outputs/apk/debug/app-debug.apk"
if [ ! -f "$APK" ]; then
  echo "CHYBA: Build sa skončil bez výsledného APK."
  exit 1
fi

echo "=== APK VYTVORENÉ ==="
ls -lh "$APK"

if [ -d /sdcard/Download ] && [ -w /sdcard/Download ]; then
  cp "$APK" /sdcard/Download/FakeGPSPro.apk
  echo "APK uložené: /sdcard/Download/FakeGPSPro.apk"
else
  echo "APK je v: $APK"
  echo "Úložisko nie je dostupné. V Termuxe spusti termux-setup-storage a povoľ prístup."
fi

echo
echo "=== AKTIVÁCIA ==="
echo "1. Nainštaluj FakeGPSPro.apk."
echo "2. Nastavenia -> O telefóne -> 7x Číslo zostavy."
echo "3. Možnosti pre vývojárov -> Aplikácia na simulovanie polohy."
echo "4. Vyber FakeGPS Pro."
echo "5. Udeľ oprávnenia a v aplikácii nastav súradnice."
