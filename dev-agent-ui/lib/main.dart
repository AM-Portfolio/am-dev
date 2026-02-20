import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:http/http.dart' as http; // Import http
import 'dart:convert';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Dev Agent God Mode',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: Colors.deepPurple,
          brightness: Brightness.dark,
        ),
        useMaterial3: true,
        fontFamily: GoogleFonts.robotoMono().fontFamily,
      ),
      home: const DashboardPage(),
    );
  }
}

class DashboardPage extends StatefulWidget {
  const DashboardPage({super.key});

  @override
  State<DashboardPage> createState() => _DashboardPageState();
}

class _DashboardPageState extends State<DashboardPage> {
  final TextEditingController _promptController = TextEditingController();
  final TextEditingController _repoUrlController = TextEditingController(); // Added controller for Repository URL
  final TextEditingController _repoPathController = TextEditingController(); // Added controller for Repository Path
  final TextEditingController _resumeIdController = TextEditingController(); // Added controller for Resume Job ID
  final List<String> _logs = [];
  WebSocketChannel? _channel;
  String? _jobId;
  bool _isLoading = false;

  void _connect(String jobId) {
    // Connect to WebSocket using localhost for consistency
    _channel = WebSocketChannel.connect(
      Uri.parse('ws://localhost:8000/ws/$jobId'),
    );

    _channel!.stream.listen(
      (message) {
        // Message could be string or bytes
        final data = jsonDecode(message);
        setState(() {
          _logs.add("[${data['level']}] ${data['message']}");
        });
      },
      onError: (error) {
        setState(() {
           _logs.add("[ERROR] WebSocket error: $error");
        });
      },
      onDone: () {
         setState(() {
           _logs.add("[INFO] WebSocket closed.");
        });
      },
    );
  }
  
  Future<void> _launchAgent() async {
     setState(() {
       _isLoading = true;
       _logs.clear();
       _logs.add("🚀 Launching Agent...");
     });

     try {
       // Call API to create a job (POST with JSON body)
       // Assuming running on localhost:8000
       final response = await http.post(
         Uri.parse('http://localhost:8000/api/v1/jobs'),
         headers: {
           'X-API-Key': 'godmode-v1', // Using key from LOCAL_DEV.md
           'Content-Type': 'application/json',
         },
         body: jsonEncode({
           "user_input": _promptController.text,
           "repo_url": _repoUrlController.text.isNotEmpty ? _repoUrlController.text : null,
           "repo_path": _repoPathController.text.isNotEmpty ? _repoPathController.text : null,
           "resume_job_id": _resumeIdController.text.isNotEmpty ? _resumeIdController.text : null,
         }),
       );

       if (response.statusCode == 200) {
         final data = jsonDecode(response.body);
         final jobId = data['job_id'];
         final status = data['status'] ?? "submitted";
         
         setState(() {
           _jobId = jobId;
           _logs.add("✅ Job ${status == 'resumed' ? 'Resumed' : 'Created'}: $jobId");
         });
         
         // Connect to stream
         _connect(jobId);
       } else {
         setState(() {
           _logs.add("❌ Failed to launch agent: ${response.statusCode} - ${response.body}");
         });
       }
     } catch (e) {
       setState(() {
         _logs.add("❌ Error connecting to backend: $e"); 
       });
     } finally {
       setState(() {
         _isLoading = false;
       });
     }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("🛡️ God Mode Dashboard")),
      body: Row(
        children: [
          // Left: Controls
          Expanded(
            flex: 1,
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                children: [
                   // Repo URL 
                   TextField(
                    controller: _repoUrlController,
                    decoration: const InputDecoration(
                      labelText: "Repository URL (Optional)",
                      border: OutlineInputBorder(),
                      hintText: "https://github.com/user/repo",
                    ),
                  ),
                  const SizedBox(height: 16),
                  
                  // Local Path
                  TextField(
                    controller: _repoPathController,
                    decoration: const InputDecoration(
                      labelText: "Local Path / Workspace (Optional)",
                      border: OutlineInputBorder(),
                      hintText: "C:/path/to/repo",
                    ),
                  ),
                  const SizedBox(height: 16),

                   // Resume Job ID
                   TextField(
                    controller: _resumeIdController,
                    decoration: const InputDecoration(
                      labelText: "Resume Previous Job ID (Optional)",
                      border: OutlineInputBorder(),
                      hintText: "e.g., 550e8400-e29b-41d4-a716-446655440000",
                    ),
                  ),
                  const SizedBox(height: 16),
                  
                  TextField(
                    controller: _promptController,
                    decoration: const InputDecoration(
                      labelText: "Mission Objective",
                      border: OutlineInputBorder(),
                    ),
                    maxLines: 4,
                  ),
                  const SizedBox(height: 16),
                  ElevatedButton.icon(
                    icon: _isLoading 
                        ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2)) 
                        : const Icon(Icons.rocket_launch),
                    label: Text(_isLoading ? "Launching..." : "Launch Agent"),
                    onPressed: _isLoading ? null : _launchAgent,
                  ),
                ],
              ),
            ),
          ),
          // Right: Logs (Matrix Style)
          Expanded(
            flex: 2,
            child: Container(
              color: Colors.black,
              child: ListView.builder(
                itemCount: _logs.length,
                itemBuilder: (context, index) {
                  return Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                    child: Text(
                      _logs[index],
                      style: const TextStyle(color: Colors.greenAccent),
                    ),
                  );
                },
              ),
            ),
          ),
        ],
      ),
    );
  }
}
