import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'pairing/generate_qr_screen.dart';
import 'pairing/scan_qr_screen.dart';

class RadarHomeScreen extends StatefulWidget {
  const RadarHomeScreen({super.key});

  @override
  State<RadarHomeScreen> createState() => _RadarHomeScreenState();
}

class _RadarHomeScreenState extends State<RadarHomeScreen> with SingleTickerProviderStateMixin {
  late AnimationController _pulseController;
  
  // The Local API URL for the background OS Engine (Rust/Kotlin)
  static const String localApiBase = "http://127.0.0.1:8766";
  
  String myPublicKey = "Loading...";
  Map<String, dynamic> activeRoster = {};
  Timer? _rosterPollTimer;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 4),
    )..repeat();
    
    // 1. Fetch our real Curve25519 identity for QR generation
    _fetchMyPublicKey();
    
    // 2. Poll the Rust/Kotlin engine every 2 seconds to get live mesh connections
    _rosterPollTimer = Timer.periodic(const Duration(seconds: 2), (_) {
      _fetchActiveRoster();
    });
  }
  
  Future<void> _fetchMyPublicKey() async {
    try {
      final response = await http.get(Uri.parse("\$localApiBase/identity"));
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        setState(() {
          myPublicKey = data['pub_key'];
        });
      } else {
        setState(() => myPublicKey = "API Error: \${response.statusCode}");
      }
    } catch (e) {
      setState(() => myPublicKey = "Engine Offline or Unreachable");
    }
  }
  
  Future<void> _fetchActiveRoster() async {
    try {
      final response = await http.get(Uri.parse("\$localApiBase/roster"));
      if (response.statusCode == 200) {
        final Map<String, dynamic> data = jsonDecode(response.body);
        if (mounted) {
          setState(() {
            activeRoster = data;
          });
        }
      }
    } catch (e) {
      // Background Engine isn't running yet, ignore polling error silently
    }
  }
  
  Future<void> _addTrustedDevice(String pubKey, String deviceName) async {
    try {
      final response = await http.post(
        Uri.parse("\$localApiBase/roster/add"),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({
          "pub_key": pubKey,
          "name": deviceName,
        }),
      );
      
      if (mounted) {
        if (response.statusCode == 200) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text("✅ Paired securely with: \$deviceName", style: const TextStyle(fontWeight: FontWeight.bold))),
          );
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text("❌ Pairing rejected by engine: \${response.statusCode}")),
          );
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("❌ Connection to OS Engine lost. Is the daemon running?")),
        );
      }
    }
  }

  @override
  void dispose() {
    _pulseController.dispose();
    _rosterPollTimer?.cancel();
    super.dispose();
  }

  // Draw the spinning orbit of active devices on the Mesh
  List<Widget> _buildOrbitingDevices() {
    List<Widget> children = [];
    
    // Add the center device (US)
    children.add(
      const Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.laptop_mac, size: 40, color: Colors.white),
          SizedBox(height: 8),
          Text("This Device", style: TextStyle(fontSize: 12, color: Colors.white70)),
        ],
      )
    );

    // If no devices are connected, return just us
    if (activeRoster.isEmpty) {
      return children;
    }

    // Distribute connected devices dynamically around the 300x300 circle
    int i = 0;
    activeRoster.forEach((pubKey, peerInfo) {
      final String name = peerInfo['name'] ?? "Unknown";
      // Dynamic positioning logic would go here based on angle
      // For now, stack them vertically on the left side of the radar
      children.add(
        Positioned(
          left: 40,
          top: 40.0 + (i * 80.0),
          child: Column(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: const Color(0xFF3B82F6).withOpacity(0.2),
                  shape: BoxShape.circle,
                  border: Border.all(color: const Color(0xFF3B82F6), width: 2),
                ),
                child: const Icon(Icons.smartphone, color: Color(0xFF3B82F6), size: 24),
              ),
              const SizedBox(height: 4),
              Text(name, style: const TextStyle(fontSize: 10, color: Color(0xFF3B82F6))),
            ],
          ),
        ),
      );
      i++;
    });
    
    return children;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF12121A),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: const Text('Local Mesh', style: TextStyle(fontWeight: FontWeight.w600, color: Colors.white)),
        actions: [
          IconButton(
            icon: const Icon(Icons.qr_code, color: Colors.white70),
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (context) => GenerateQrScreen(
                    myPublicKey: myPublicKey,
                    myDeviceName: "Ezio Device", 
                  ),
                ),
              );
            },
          ),
          IconButton(
            icon: const Icon(Icons.settings, color: Colors.white70),
            onPressed: () {},
          ),
        ],
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // The Radar View
            Container(
              width: 300,
              height: 300,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                border: Border.all(color: const Color(0xFF00FF9D).withOpacity(0.3), width: 1),
                color: const Color(0xFF1A1A24),
              ),
              child: Stack(
                alignment: Alignment.center,
                children: _buildOrbitingDevices(),
              ),
            ),
            
            const SizedBox(height: 60),
            
            // Status Card
            Container(
              margin: const EdgeInsets.symmetric(horizontal: 24),
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: const Color(0xFF1A1A24),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: Colors.white10),
              ),
              child: Row(
                children: [
                  Icon(
                    activeRoster.isNotEmpty ? Icons.check_circle : Icons.radio_button_unchecked, 
                    color: activeRoster.isNotEmpty ? const Color(0xFF00FF9D) : Colors.white30
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          activeRoster.isNotEmpty ? "Mesh Active" : "Waiting for Peers...", 
                          style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.white)
                        ),
                        Text(
                          activeRoster.isNotEmpty ? "\${activeRoster.length} devices secured via Curve25519" : "mDNS Discovery & E2EE running", 
                          style: const TextStyle(fontSize: 12, color: Colors.white54)
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) => ScanQrScreen(
                onScanned: (pubKey, name) {
                  // Pass the QR Code payload securely into the OS engine via Local API!
                  _addTrustedDevice(pubKey, name);
                },
              ),
            ),
          );
        },
        backgroundColor: const Color(0xFF00FF9D),
        foregroundColor: Colors.black,
        icon: const Icon(Icons.qr_code_scanner),
        label: const Text("Scan to Pair", style: TextStyle(fontWeight: FontWeight.bold)),
      ),
    );
  }
}
