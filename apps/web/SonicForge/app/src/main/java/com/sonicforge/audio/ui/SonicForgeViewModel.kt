package com.sonicforge.audio.ui

import android.content.Context
import android.net.Uri
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.sonicforge.audio.audio.AudioBuffer
import com.sonicforge.audio.audio.WavAudio
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.File

class SonicForgeViewModel : ViewModel() {

    private val _state = MutableStateFlow(EditorState())
    val state: StateFlow<EditorState> = _state.asStateFlow()

    suspend fun importUri(context: Context, uri: Uri) {
        _state.value = _state.value.copy(loading = true, message = null)
        try {
            val result = withContext(Dispatchers.IO) {
                val name = queryName(context, uri)
                val cache = File(context.cacheDir, "source_${System.currentTimeMillis()}.wav")
                context.contentResolver.openInputStream(uri).use { input ->
                    requireNotNull(input) { "Cannot open selected file" }
                    cache.outputStream().use { output -> input.copyTo(output, 64 * 1024) }
                }
                val audio = WavAudio.read(cache)
                Triple(name, cache, audio)
            }
            val stats = WavAudio.stats(result.third)
            _state.value = EditorState(
                name = result.first,
                sourceUri = uri,
                audio = result.third,
                stats = stats,
                message = "Imported ${result.third.durationMs / 1000}s WAV"
            )
        } catch (e: Exception) {
            _state.value = _state.value.copy(loading = false, message = "Import failed: ${e.message}")
        }
    }

    fun setGain(db: Float) {
        val s = _state.value
        _state.value = s.copy(gainDb = db, previewAudio = preview(s.audio, db, s.compressor))
    }

    fun normalize() {
        val s = _state.value
        val audio = s.audio ?: return
        val normalized = WavAudio.normalizePeak(audio, -1f)
        val gain = WavAudio.stats(normalized).peakDbfs - s.stats.peakDbfs
        _state.value = s.copy(
            gainDb = gain,
            previewAudio = normalized,
            clipping = WavAudio.stats(normalized).clippingSamples > 0
        )
    }

    fun preset(p: Preset) {
        val s = _state.value
        val gain = when (p) {
            Preset.CLEAN_VOICE -> 4f
            Preset.PODCAST -> 3f
            Preset.LOUDER -> 8f
            Preset.MUSIC -> 1.5f
            Preset.VOICE_MESSAGE -> 5f
        }
        val comp = p != Preset.MUSIC
        _state.value = s.copy(gainDb = gain, compressor = comp, previewAudio = preview(s.audio, gain, comp))
    }

    private fun preview(audio: AudioBuffer?, gain: Float, compressor: Boolean): AudioBuffer? {
        if (audio == null) return null
        var x = WavAudio.gain(audio, gain)
        if (compressor) x = WavAudio.compressor(x)
        x = WavAudio.limiter(x, -1f)
        return x
    }

    suspend fun process() {
        val s = _state.value
        val audio = s.audio ?: return
        _state.value = s.copy(loading = true)
        withContext(Dispatchers.Default) {
            var x = WavAudio.highPass(audio, 60f)
            x = WavAudio.gain(x, s.gainDb)
            if (s.compressor) x = WavAudio.compressor(x)
            x = WavAudio.limiter(x, -1f)
            x = WavAudio.fade(x, 5, 5)
            val stats = WavAudio.stats(x)
            _state.value = _state.value.copy(
                loading = false,
                previewAudio = x,
                stats = stats,
                clipping = stats.clippingSamples > 0,
                gainReduction = if (s.compressor) 0.35f else 0.0f,
                message = "Processing complete"
            )
        }
    }

    suspend fun export(context: Context) {
        val s = _state.value
        val audio = s.previewAudio ?: preview(s.audio, s.gainDb, s.compressor)
        if (audio == null) {
            _state.value = s.copy(message = "Nothing to export")
            return
        }
        _state.value = s.copy(loading = true)
        try {
            val output = withContext(Dispatchers.IO) {
                val dir = File(context.getExternalFilesDir(null), "exports").apply { mkdirs() }
                val safe = s.name.substringBeforeLast('.')
                    .replace(Regex("[^A-Za-z0-9._-]"), "_")
                    .ifBlank { "audio" }
                File(dir, "${safe}_sonicforge_${System.currentTimeMillis()}.wav").also {
                    WavAudio.write(it, audio)
                }
            }
            _state.value = _state.value.copy(loading = false, message = "Exported: ${output.absolutePath}")
        } catch (e: Exception) {
            _state.value = _state.value.copy(loading = false, message = "Export failed: ${e.message}")
        }
    }

    fun resetProcessing() {
        val s = _state.value
        _state.value = s.copy(
            gainDb = 0f,
            compressor = false,
            previewAudio = null,
            stats = s.audio?.let(WavAudio::stats) ?: s.stats,
            clipping = false,
            gainReduction = 0f
        )
    }

    fun reset() {
        _state.value = EditorState()
    }

    fun clearMessage() {
        _state.value = _state.value.copy(message = null)
    }

    private fun queryName(context: Context, uri: Uri): String {
        val projection = arrayOf(android.provider.OpenableColumns.DISPLAY_NAME)
        context.contentResolver.query(uri, projection, null, null, null)?.use { c ->
            if (c.moveToFirst()) return c.getString(0) ?: "audio.wav"
        }
        return uri.lastPathSegment ?: "audio.wav"
    }
}
