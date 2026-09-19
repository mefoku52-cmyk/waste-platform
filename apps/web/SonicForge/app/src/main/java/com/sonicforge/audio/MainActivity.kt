package com.sonicforge.audio

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import com.sonicforge.audio.ui.SonicForgeApp
import com.sonicforge.audio.ui.theme.SonicForgeTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            SonicForgeTheme {
                SonicForgeApp()
            }
        }
    }
}
