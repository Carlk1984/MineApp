import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/auth_service.dart';
import '../services/api_service.dart';
import '../models/record.dart';

class RecordsScreen extends StatefulWidget {
  const RecordsScreen({super.key});

  @override
  State<RecordsScreen> createState() => _RecordsScreenState();
}

class _RecordsScreenState extends State<RecordsScreen> {
  List<Record> _records = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadRecords();
  }

  Future<void> _loadRecords() async {
    setState(() => _isLoading = true);
    
    try {
      final authService = context.read<AuthService>();
      final apiService = context.read<ApiService>();
      final authHeader = authService.getAuthHeader();
      
      if (authHeader != null) {
        final records = await apiService.getRecords(authHeader.substring(7));
        setState(() {
          _records = records;
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() => _isLoading = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error loading records: $e')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('KPI Records'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadRecords,
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _records.isEmpty
              ? const Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.assignment, size: 64, color: Colors.grey),
                      SizedBox(height: 16),
                      Text('No records found'),
                    ],
                  ),
                )
              : ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: _records.length,
                  itemBuilder: (context, index) {
                    final record = _records[index];
                    return Card(
                      margin: const EdgeInsets.only(bottom: 8),
                      child: ListTile(
                        title: Text(record.module),
                        subtitle: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('Manager: ${record.managerOnDuty}'),
                            Text('Status: ${record.approvalStatus.toUpperCase()}'),
                            Text('Date: ${record.timestamp.toString().split('.')[0]}'),
                          ],
                        ),
                        trailing: _buildStatusChip(record.approvalStatus),
                        onTap: () => _showRecordDetails(record),
                      ),
                    );
                  },
                ),
      floatingActionButton: FloatingActionButton(
        onPressed: _showCreateRecordDialog,
        child: const Icon(Icons.add),
      ),
    );
  }

  Widget _buildStatusChip(String status) {
    Color color;
    switch (status) {
      case 'approved':
        color = Colors.green;
        break;
      case 'rejected':
        color = Colors.red;
        break;
      default:
        color = Colors.orange;
    }
    
    return Chip(
      label: Text(
        status.toUpperCase(),
        style: const TextStyle(color: Colors.white, fontSize: 12),
      ),
      backgroundColor: color,
    );
  }

  void _showRecordDetails(Record record) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(record.module),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Manager on Duty: ${record.managerOnDuty}'),
            Text('Status: ${record.approvalStatus}'),
            Text('Timestamp: ${record.timestamp}'),
            const SizedBox(height: 16),
            const Text('Data:', style: TextStyle(fontWeight: FontWeight.bold)),
            Text(record.data.toString()),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Close'),
          ),
        ],
      ),
    );
  }

  void _showCreateRecordDialog() {
    final moduleController = TextEditingController();
    final managerController = TextEditingController();
    final dataController = TextEditingController();

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Create New Record'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: moduleController,
              decoration: const InputDecoration(labelText: 'Module'),
            ),
            TextField(
              controller: managerController,
              decoration: const InputDecoration(labelText: 'Manager on Duty'),
            ),
            TextField(
              controller: dataController,
              decoration: const InputDecoration(labelText: 'Data (JSON format)'),
              maxLines: 3,
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () async {
              try {
                final authService = context.read<AuthService>();
                final apiService = context.read<ApiService>();
                final authHeader = authService.getAuthHeader();
                
                if (authHeader != null) {
                  await apiService.createRecord(
                    authHeader.substring(7),
                    {
                      'module': moduleController.text,
                      'manager_on_duty': managerController.text,
                      'data': {'note': dataController.text},
                    },
                  );
                  
                  if (mounted) {
                    Navigator.of(context).pop();
                    _loadRecords();
                  }
                }
              } catch (e) {
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('Error creating record: $e')),
                  );
                }
              }
            },
            child: const Text('Create'),
          ),
        ],
      ),
    );
  }
}
