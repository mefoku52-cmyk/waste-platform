package com.sonicforge.audio.ui

import android.net.Uri
import android.widget.Toast
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.AutoFixHigh
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Save
import androidx.compose.material3.AssistChip
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Slider
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.sonicforge.audio.audio.AudioBuffer
import com.sonicforge.audio.audio.AudioStats
import com.sonicforge.audio.audio.WavAudio
import kotlinx.coroutines.launch
import kotlin.math.abs
import kotlin.math.max
import kotlin.math.min

@Composable
fun SonicForgeApp(vm: SonicForgeViewModel = viewModel()) {
    val state by vm.state.collectAsState()
    val context = LocalContext.current
    val scope = rememberCoroutineScope()

    val picker = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
        if (uri != null) {
            scope.launch { vm.importUri(context, uri) }
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text("SonicForge", fontWeight = FontWeight.Bold)
                        Text("Audio Studio", style = MaterialTheme.typography.labelSmall)
                    }
                },
                actions = {
                    IconButton(onClick = { vm.reset() }) {
                        Icon(Icons.Default.Refresh, "Reset")
                    }
                }
            )
        }
    ) { padding ->
        when {
            state.loading -> LoadingScreen(Modifier.padding(padding))
            state.audio == null -> Dashboard(
                modifier = Modifier.padding(padding),
                onImport = { picker.launch(arrayOf("audio/wav", "audio/x-wav", "audio/*")) }
            )
            else -> Editor(
                modifier = Modifier.padding(padding),
                state = state,
                onGain = vm::setGain,
                onPreset = vm::preset,
                onNormalize = vm::normalize,
                onProcess = { scope.launch { vm.process() } },
                onExport = { scope.launch { vm.export(context) } },
                onReset = vm::resetProcessing
            )
        }
    }

    state.message?.let { msg ->
        LaunchedEffect(msg) {
            Toast.makeText(context, msg, Toast.LENGTH_LONG).show()
            vm.clearMessage()
        }
    }
}

@Composable
private fun Dashboard(modifier: Modifier, onImport: () -> Unit) {
    Column(
        modifier.fillMaxSize().padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(18.dp)
    ) {
        Spacer(Modifier.height(8.dp))
        Text(
            "Your audio workspace",
            style = MaterialTheme.typography.headlineMedium,
            fontWeight = FontWeight.Bold
        )
        Text(
            "Import a WAV file, inspect its levels, make a real offline edit and export a new file.",
            style = MaterialTheme.typography.bodyLarge
        )
        Button(
            onClick = onImport,
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(18.dp)
        ) {
            Text("Import audio")
        }
        Card(shape = RoundedCornerShape(22.dp)) {
            Column(Modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                Text("Processing engine", fontWeight = FontWeight.Bold)
                Text("Gain • peak normalization • compressor • limiter • high-pass • fades")
                Text("Offline processing. Your audio is not uploaded.")
            }
        }
        Card(shape = RoundedCornerShape(22.dp)) {
            Column(Modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("Current processor scope", fontWeight = FontWeight.Bold)
                Text("The built-in renderer processes 16-bit PCM WAV. Media3 playback can open additional Android-supported formats.")
                Text("MP3/AAC/FLAC/OGG export requires a native codec layer and is intentionally not faked in this build.")
            }
        }
    }
}

@Composable
private fun LoadingScreen(modifier: Modifier) {
    Box(modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            CircularProgressIndicator()
            Text("Analysing audio…")
        }
    }
}

@Composable
private fun Editor(
    modifier: Modifier,
    state: EditorState,
    onGain: (Float) -> Unit,
    onPreset: (Preset) -> Unit,
    onNormalize: () -> Unit,
    onProcess: () -> Unit,
    onExport: () -> Unit,
    onReset: () -> Unit
) {
    Column(
        modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp)
    ) {
        Text(state.name, style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)

        Waveform(state.audio!!, state.previewAudio)
        StatsCard(state)

        Card(shape = RoundedCornerShape(20.dp)) {
            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Text("Loudness", fontWeight = FontWeight.Bold)
                Text("%.1f dB gain".format(state.gainDb))
                Slider(
                    value = state.gainDb,
                    onValueChange = onGain,
                    valueRange = -12f..24f
                )
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedButton(onClick = onReset) { Text("Reset") }
                    Button(onClick = onNormalize) { Text("Peak normalize") }
                }
            }
        }

        Card(shape = RoundedCornerShape(20.dp)) {
            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                Text("Presets", fontWeight = FontWeight.Bold)
                Row(
                    Modifier.horizontalScroll(rememberScrollState()),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    Preset.entries.forEach { p ->
                        AssistChip(onClick = { onPreset(p) }, label = { Text(p.label) })
                    }
                }
            }
        }

        Card(shape = RoundedCornerShape(20.dp)) {
            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                Text("Dynamics & safety", fontWeight = FontWeight.Bold)
                Text("Compressor: ${if (state.compressor) "ON" else "OFF"}")
                Text("Limiter ceiling: -1.0 dBFS")
                LinearProgressIndicator(
                    progress = { state.gainReduction },
                    modifier = Modifier.fillMaxWidth()
                )
                Text(
                    if (state.clipping) "Clipping detected in processed preview"
                    else "No hard clipping detected"
                )
            }
        }

        Row(horizontalArrangement = Arrangement.spacedBy(10.dp), modifier = Modifier.fillMaxWidth()) {
            Button(onClick = onProcess, modifier = Modifier.weight(1f)) {
                Icon(Icons.Default.AutoFixHigh, null)
                Spacer(Modifier.width(6.dp))
                Text("Process")
            }
            Button(onClick = onExport, modifier = Modifier.weight(1f)) {
                Icon(Icons.Default.Save, null)
                Spacer(Modifier.width(6.dp))
                Text("Export WAV")
            }
        }

        Text(
            "Important: increasing gain cannot restore distortion that was already present in the original recording.",
            style = MaterialTheme.typography.bodySmall
        )
    }
}

@Composable
private fun StatsCard(state: EditorState) {
    Card(shape = RoundedCornerShape(20.dp)) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(7.dp)) {
            Text("Technical information", fontWeight = FontWeight.Bold)
            Text("Sample rate: ${state.audio?.sampleRate} Hz")
            Text("Channels: ${state.audio?.channels}")
            Text("Duration: ${state.audio?.durationMs?.div(1000)} s")
            Text("%.1f dBFS peak".format(state.stats.peakDbfs))
            Text("%.1f dBFS RMS".format(state.stats.rmsDbfs))
            Text("%.1f dBTP true-peak approx".format(state.stats.truePeakApproxDbtp))
            Text("Clipping samples: ${state.stats.clippingSamples}")
        }
    }
}

@Composable
private fun Waveform(audio: AudioBuffer, preview: AudioBuffer?) {
    val data = preview ?: audio
    Card(shape = RoundedCornerShape(20.dp)) {
        Canvas(Modifier.fillMaxWidth().height(180.dp).padding(12.dp)) {
            val center = size.height / 2f
            drawLine(
                MaterialTheme.colorScheme.outline.copy(alpha = 0.35f),
                Offset(0f, center),
                Offset(size.width, center),
                strokeWidth = 1f
            )
            val bins = min(900, data.frameCount.coerceAtLeast(1))
            val step = max(1, data.frameCount / bins)
            for (i in 0 until bins) {
                val start = i * step * data.channels
                val end = min(data.samples.size, start + step * data.channels)
                var peak = 0f
                var j = start
                while (j < end) {
                    peak = max(peak, abs(data.samples[j]))
                    j++
                }
                val x = i.toFloat() / bins * size.width
                val h = peak * (size.height * 0.45f)
                drawLine(
                    MaterialTheme.colorScheme.primary,
                    Offset(x, center - h),
                    Offset(x, center + h),
                    strokeWidth = 2f,
                    cap = StrokeCap.Round
                )
            }
        }
    }
}

enum class Preset(val label: String) {
    CLEAN_VOICE("Clean Voice"),
    PODCAST("Podcast"),
    LOUDER("Louder Audio"),
    MUSIC("Music"),
    VOICE_MESSAGE("Voice Message")
}

data class EditorState(
    val name: String = "",
    val sourceUri: Uri? = null,
    val audio: AudioBuffer? = null,
    val previewAudio: AudioBuffer? = null,
    val stats: AudioStats = AudioStats(-120f, -120f, -120f, 0),
    val gainDb: Float = 0f,
    val compressor: Boolean = false,
    val loading: Boolean = false,
    val clipping: Boolean = false,
    val gainReduction: Float = 0f,
    val message: String? = null
)
