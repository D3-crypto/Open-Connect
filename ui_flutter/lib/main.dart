import 'package:flutter/material.dart';
import 'screens/radar_home_screen.dart';

void main() {
  runApp(const OpenConnectApp());
}

class OpenConnectApp extends StatelessWidget {
  const OpenConnectApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'OpenConnect',
      theme: ThemeData(
        brightness: Brightness.dark,
        scaffoldBackgroundColor: const Color(0xFF0D0D12), // Deep hardware black
        primaryColor: const Color(0xFF00FF9D), // Cyberpunk/Terminal Green
        fontFamily: 'Inter', // Sleek, technical font
        colorScheme: const ColorScheme.dark(
          primary: Color(0xFF00FF9D),
          secondary: Color(0xFF3B82F6), // Accent Blue
          surface: Color(0xFF1A1A24), // Card background
        ),
      ),
      home: const RadarHomeScreen(),
    );
  }
}
