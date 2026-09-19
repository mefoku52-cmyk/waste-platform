package com.sonicforge.audio.audio

import android.content.Context
import android.net.Uri
import androidx.media3.common.MediaItem
import androidx.media3.exoplayer.ExoPlayer

class AudioPlayer(context: Context) {
    private val player = ExoPlayer.Builder(context).build()

    fun play(uri: Uri) {
        player.setMediaItem(MediaItem.fromUri(uri))
        player.prepare()
        player.play()
    }

    fun pause() = player.pause()
    fun stop() = player.stop()
    fun release() = player.release()
    fun isPlaying(): Boolean = player.isPlaying
    fun durationMs(): Long = player.duration.coerceAtLeast(0L)
    fun positionMs(): Long = player.currentPosition
    fun seekTo(ms: Long) = player.seekTo(ms)
}
