package com.sonicforge.audio.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val DarkScheme = darkColorScheme(
    primary = Color(0xFF66E6C2),
    onPrimary = Color(0xFF00382E),
    secondary = Color(0xFF9AD8FF),
    tertiary = Color(0xFFD2B8FF),
    background = Color(0xFF080A0D),
    surface = Color(0xFF111419),
    surfaceVariant = Color(0xFF1A1F25)
)

private val LightScheme = lightColorScheme(
    primary = Color(0xFF006B59),
    secondary = Color(0xFF00658F),
    tertiary = Color(0xFF6D4DA1)
)

@Composable
fun SonicForgeTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit
) {
    MaterialTheme(
        colorScheme = if (darkTheme) DarkScheme else LightScheme,
        content = content
    )
}
