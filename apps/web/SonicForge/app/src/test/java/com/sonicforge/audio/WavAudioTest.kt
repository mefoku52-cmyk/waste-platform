package com.sonicforge.audio

import com.sonicforge.audio.audio.AudioBuffer
import com.sonicforge.audio.audio.WavAudio
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import kotlin.math.abs
import kotlin.math.pow

class WavAudioTest {

    @Test
    fun gainChangesAmplitudePredictably() {
        val source = AudioBuffer(48000, 1, floatArrayOf(0.25f, -0.25f))
        val out = WavAudio.gain(source, 6f)
        val expected = 0.25f * 10.0.pow(6.0 / 20.0).toFloat()
        assertEquals(expected, abs(out.samples[0]), 0.001f)
    }

    @Test
    fun limiterNeverExceedsCeiling() {
        val source = AudioBuffer(48000, 1, floatArrayOf(1f, -1f, 0.2f))
        val out = WavAudio.limiter(source, -1f)
        val ceiling = 10.0.pow(-1.0 / 20.0).toFloat()
        assertTrue(out.samples.all { abs(it) <= ceiling + 0.0001f })
    }

    @Test
    fun statsDetectsClipping() {
        val source = AudioBuffer(48000, 1, floatArrayOf(0f, 0.99999f, -1f))
        assertEquals(1, WavAudio.stats(source).clippingSamples)
    }

    @Test
    fun normalizeTargetsPeak() {
        val source = AudioBuffer(48000, 1, floatArrayOf(0.5f, -0.25f))
        val out = WavAudio.normalizePeak(source, -1f)
        assertEquals(-1f, WavAudio.stats(out).peakDbfs, 0.01f)
    }
}
