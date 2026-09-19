package com.sonicforge.audio.audio

import java.io.BufferedInputStream
import java.io.BufferedOutputStream
import java.io.File
import java.nio.ByteBuffer
import java.nio.ByteOrder
import kotlin.math.abs
import kotlin.math.max
import kotlin.math.min
import kotlin.math.pow

data class AudioBuffer(
    val sampleRate: Int,
    val channels: Int,
    val samples: FloatArray
) {
    val frameCount: Int get() = samples.size / channels
    val durationMs: Long get() = frameCount * 1000L / sampleRate
}

data class AudioStats(
    val peakDbfs: Float,
    val truePeakApproxDbtp: Float,
    val rmsDbfs: Float,
    val clippingSamples: Int
)

object WavAudio {

    fun read(file: File, maxFrames: Int = 2_500_000): AudioBuffer {
        BufferedInputStream(file.inputStream(), 64 * 1024).use { input ->
            fun readIntLE(): Int {
                val b = ByteArray(4)
                if (input.read(b) != 4) error("Unexpected end of WAV")
                return ByteBuffer.wrap(b).order(ByteOrder.LITTLE_ENDIAN).int
            }
            fun readShortLE(): Int {
                val b = ByteArray(2)
                if (input.read(b) != 2) error("Unexpected end of WAV")
                return ByteBuffer.wrap(b).order(ByteOrder.LITTLE_ENDIAN).short.toInt()
            }

            val riff = ByteArray(4)
            if (input.read(riff) != 4 || String(riff) != "RIFF") error("Not a RIFF/WAV file")
            readIntLE()
            val wave = ByteArray(4)
            if (input.read(wave) != 4 || String(wave) != "WAVE") error("Not a WAVE file")

            var channels = 0
            var sampleRate = 0
            var bits = 0
            var audioFormat = 0
            var dataSize = -1

            while (dataSize < 0) {
                val id = ByteArray(4)
                if (input.read(id) != 4) break
                val size = readIntLE()
                when (String(id)) {
                    "fmt " -> {
                        audioFormat = readShortLE()
                        channels = readShortLE()
                        sampleRate = readIntLE()
                        readIntLE()   // byte rate
                        readShortLE() // block align
                        bits = readShortLE()
                        val remaining = size - 16
                        if (remaining > 0) input.skip(remaining.toLong())
                    }
                    "data" -> {
                        dataSize = size
                        break
                    }
                    else -> input.skip(size.toLong() + (size and 1))
                }
            }

            require(audioFormat == 1) { "Only PCM WAV is supported by the processor" }
            require(channels in 1..2) { "Only mono/stereo WAV is supported" }
            require(bits == 16) { "Processor requires 16-bit PCM WAV" }
            require(dataSize > 0) { "WAV has no audio data" }

            val frames = min(dataSize / (channels * 2), maxFrames)
            val raw = ByteArray(frames * channels * 2)
            var offset = 0
            while (offset < raw.size) {
                val n = input.read(raw, offset, raw.size - offset)
                if (n <= 0) break
                offset += n
            }
            val samples = FloatArray(offset / 2)
            val bb = ByteBuffer.wrap(raw, 0, offset).order(ByteOrder.LITTLE_ENDIAN)
            var i = 0
            while (bb.remaining() >= 2) {
                samples[i++] = bb.short / 32768f
            }
            return AudioBuffer(sampleRate, channels, samples.copyOf(i))
        }
    }

    fun write(file: File, audio: AudioBuffer) {
        require(audio.channels in 1..2)
        BufferedOutputStream(file.outputStream(), 64 * 1024).use { out ->
            val dataBytes = audio.samples.size * 2
            val riffSize = 36 + dataBytes
            fun intLE(v: Int) {
                out.write(byteArrayOf(
                    (v and 0xff).toByte(),
                    ((v shr 8) and 0xff).toByte(),
                    ((v shr 16) and 0xff).toByte(),
                    ((v shr 24) and 0xff).toByte()
                ))
            }
            fun shortLE(v: Int) {
                out.write(byteArrayOf((v and 0xff).toByte(), ((v shr 8) and 0xff).toByte()))
            }
            out.write("RIFF".toByteArray()); intLE(riffSize)
            out.write("WAVE".toByteArray())
            out.write("fmt ".toByteArray()); intLE(16)
            shortLE(1); shortLE(audio.channels)
            intLE(audio.sampleRate)
            intLE(audio.sampleRate * audio.channels * 2)
            shortLE(audio.channels * 2); shortLE(16)
            out.write("data".toByteArray()); intLE(dataBytes)
            audio.samples.forEach { s ->
                shortLE((s.coerceIn(-1f, 1f) * 32767f).toInt())
            }
        }
    }

    fun stats(audio: AudioBuffer): AudioStats {
        if (audio.samples.isEmpty()) return AudioStats(-120f, -120f, -120f, 0)
        var peak = 0f
        var sum = 0.0
        var clipped = 0
        audio.samples.forEach { s ->
            val a = abs(s)
            peak = max(peak, a)
            if (a >= 0.9999f) clipped++
            sum += s.toDouble() * s
        }
        val rms = kotlin.math.sqrt(sum / audio.samples.size).toFloat()
        val db = { x: Float -> if (x <= 1e-9f) -120f else 20f * kotlin.math.log10(x) }
        return AudioStats(db(peak), db(min(1.0f, peak * 1.05f)), db(rms), clipped)
    }

    fun gain(audio: AudioBuffer, db: Float): AudioBuffer {
        val factor = 10.0.pow(db / 20.0).toFloat()
        return audio.copy(
            samples = audio.samples.map { (it * factor).coerceIn(-1f, 1f) }.toFloatArray()
        )
    }

    fun normalizePeak(audio: AudioBuffer, targetDbfs: Float = -1f): AudioBuffer {
        val peak = stats(audio).peakDbfs
        if (peak <= -119f) return audio
        return gain(audio, targetDbfs - peak)
    }

    fun compressor(
        audio: AudioBuffer,
        thresholdDb: Float = -18f,
        ratio: Float = 3f,
        makeupDb: Float = 0f
    ): AudioBuffer {
        val out = FloatArray(audio.samples.size)
        val makeup = 10.0.pow(makeupDb / 20.0).toFloat()
        for (i in audio.samples.indices) {
            val x = audio.samples[i]
            val sign = if (x < 0) -1f else 1f
            val db = if (abs(x) < 1e-8f) -160f else 20f * kotlin.math.log10(abs(x))
            val compressedDb = if (db > thresholdDb) thresholdDb + (db - thresholdDb) / ratio else db
            out[i] = (sign * 10.0.pow(compressedDb / 20.0).toFloat() * makeup).coerceIn(-1f, 1f)
        }
        return audio.copy(samples = out)
    }

    fun limiter(audio: AudioBuffer, ceilingDbfs: Float = -1f): AudioBuffer {
        val ceiling = 10.0.pow(ceilingDbfs / 20.0).toFloat()
        return audio.copy(
            samples = audio.samples.map { it.coerceIn(-ceiling, ceiling) }.toFloatArray()
        )
    }

    fun highPass(audio: AudioBuffer, cutoffHz: Float = 80f): AudioBuffer {
        if (cutoffHz <= 0f) return audio
        val out = FloatArray(audio.samples.size)
        val rc = 1f / (2f * Math.PI.toFloat() * cutoffHz)
        val dt = 1f / audio.sampleRate
        val alpha = rc / (rc + dt)
        for (ch in 0 until audio.channels) {
            var prevX = 0f
            var prevY = 0f
            var i = ch
            while (i < audio.samples.size) {
                val x = audio.samples[i]
                val y = alpha * (prevY + x - prevX)
                out[i] = y
                prevX = x
                prevY = y
                i += audio.channels
            }
        }
        return audio.copy(samples = out)
    }

    fun fade(audio: AudioBuffer, fadeInMs: Long, fadeOutMs: Long): AudioBuffer {
        val out = audio.samples.copyOf()
        val inFrames = (fadeInMs * audio.sampleRate / 1000L)
            .coerceAtMost(audio.frameCount.toLong()).toInt()
        val outFrames = (fadeOutMs * audio.sampleRate / 1000L)
            .coerceAtMost(audio.frameCount.toLong()).toInt()
        for (f in 0 until inFrames) {
            val g = f.toFloat() / max(1, inFrames)
            for (ch in 0 until audio.channels) out[f * audio.channels + ch] *= g
        }
        for (f in 0 until outFrames) {
            val g = (outFrames - f).toFloat() / max(1, outFrames)
            val frame = audio.frameCount - outFrames + f
            for (ch in 0 until audio.channels) out[frame * audio.channels + ch] *= g
        }
        return audio.copy(samples = out)
    }
}
