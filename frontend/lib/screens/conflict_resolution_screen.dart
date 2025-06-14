import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/hive_service.dart';
import '../models/record.dart';

class ConflictResolutionScreen extends StatefulWidget {
  const ConflictResolutionScreen({super.key});

  @override
  State<ConflictResolutionScreen> createState() => _ConflictResolutionScreenState();
}

class _ConflictResolutionScreenState extends State<ConflictResolutionScreen> {
  List<SyncConflict> _conflicts = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadConflicts();
  }

  Future<void> _loadConflicts() async {
    final hiveService = Provider.of<HiveService>(context, listen: false);
    final conflicts = await hiveService.getPendingConflicts();
    setState(() {
      _conflicts = conflicts;
      _isLoading = false;
    });
  }

  Future<void> _resolveConflict(SyncConflict conflict, Record resolvedRecord) async {
    final hiveService = Provider.of<HiveService>(context, listen: false);
    await hiveService.resolveConflict(conflict.localRecordId, resolvedRecord);
    
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Conflict resolved successfully'),
        backgroundColor: Colors.green,
      ),
    );
    
    await _loadConflicts();
  }

  Future<void> _dismissConflict(SyncConflict conflict) async {
    final hiveService = Provider.of<HiveService>(context, listen: false);
    await hiveService.dismissConflict(conflict.localRecordId);
    
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Conflict dismissed'),
        backgroundColor: Colors.orange,
      ),
    );
    
    await _loadConflicts();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Resolve Sync Conflicts'),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _conflicts.isEmpty
              ? const Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.check_circle, size: 64, color: Colors.green),
                      SizedBox(height: 16),
                      Text(
                        'No conflicts to resolve',
                        style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                      ),
                      SizedBox(height: 8),
                      Text('All your data is synchronized successfully!'),
                    ],
                  ),
                )
              : ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: _conflicts.length,
                  itemBuilder: (context, index) {
                    final conflict = _conflicts[index];
                    return _buildConflictCard(conflict);
                  },
                ),
    );
  }

  Widget _buildConflictCard(SyncConflict conflict) {
    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.warning, color: Colors.orange),
                const SizedBox(width: 8),
                Text(
                  'Sync Conflict - ${conflict.localRecord.module}',
                  style: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              'Reason: ${conflict.conflictReason}',
              style: TextStyle(color: Colors.grey[600]),
            ),
            Text(
              'Detected: ${_formatDateTime(conflict.conflictDetectedAt)}',
              style: TextStyle(color: Colors.grey[600]),
            ),
            const SizedBox(height: 16),
            
            Row(
              children: [
                Expanded(
                  child: _buildRecordPreview('Local Record', conflict.localRecord),
                ),
                const SizedBox(width: 16),
                if (conflict.serverRecord != null)
                  Expanded(
                    child: _buildRecordPreview('Server Record', conflict.serverRecord!),
                  ),
              ],
            ),
            
            const SizedBox(height: 16),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                ElevatedButton.icon(
                  onPressed: () => _resolveConflict(conflict, conflict.localRecord),
                  icon: const Icon(Icons.phone_android),
                  label: const Text('Use Local'),
                  style: ElevatedButton.styleFrom(backgroundColor: Colors.blue),
                ),
                if (conflict.serverRecord != null)
                  ElevatedButton.icon(
                    onPressed: () => _resolveConflict(conflict, conflict.serverRecord!),
                    icon: const Icon(Icons.cloud),
                    label: const Text('Use Server'),
                    style: ElevatedButton.styleFrom(backgroundColor: Colors.green),
                  ),
                ElevatedButton.icon(
                  onPressed: () => _dismissConflict(conflict),
                  icon: const Icon(Icons.close),
                  label: const Text('Dismiss'),
                  style: ElevatedButton.styleFrom(backgroundColor: Colors.grey),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildRecordPreview(String title, Record record) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        border: Border.all(color: Colors.grey[300]!),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: const TextStyle(fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          Text('Module: ${record.module}'),
          Text('Created: ${_formatDateTime(record.createdAt ?? record.timestamp)}'),
          Text('Updated: ${_formatDateTime(record.updatedAt ?? record.timestamp)}'),
          Text('Status: ${record.approvalStatus}'),
          const SizedBox(height: 8),
          const Text(
            'Data Preview:',
            style: TextStyle(fontWeight: FontWeight.w500),
          ),
          ...record.data.entries.take(3).map((entry) => 
            Text('${entry.key}: ${entry.value}', 
              style: TextStyle(fontSize: 12, color: Colors.grey[600]))),
          if (record.data.length > 3)
            Text('... and ${record.data.length - 3} more fields',
              style: TextStyle(fontSize: 12, color: Colors.grey[600])),
        ],
      ),
    );
  }

  String _formatDateTime(DateTime dateTime) {
    return '${dateTime.day}/${dateTime.month}/${dateTime.year} ${dateTime.hour}:${dateTime.minute.toString().padLeft(2, '0')}';
  }
}
