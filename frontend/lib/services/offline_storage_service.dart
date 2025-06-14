import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/record.dart';

class OfflineStorageService {
  static const String _offlineRecordsKey = 'offline_records';
  static const String _syncQueueKey = 'sync_queue';

  static Future<void> saveRecord(Record record) async {
    final prefs = await SharedPreferences.getInstance();
    
    final existingRecords = await getOfflineRecords();
    
    final recordWithId = Record(
      id: 'offline_${DateTime.now().millisecondsSinceEpoch}',
      module: record.module,
      data: record.data,
      managerOnDuty: record.managerOnDuty,
      submittedBy: record.submittedBy,
      approvalStatus: 'offline',
      timestamp: record.timestamp,
    );
    
    existingRecords.add(recordWithId);
    
    final recordsJson = existingRecords.map((r) => r.toJson()).toList();
    await prefs.setString(_offlineRecordsKey, jsonEncode(recordsJson));
    
    await addToSyncQueue(recordWithId);
  }

  static Future<List<Record>> getOfflineRecords() async {
    final prefs = await SharedPreferences.getInstance();
    final recordsString = prefs.getString(_offlineRecordsKey);
    
    if (recordsString == null) return [];
    
    final recordsJson = jsonDecode(recordsString) as List;
    return recordsJson.map((json) => Record.fromJson(json)).toList();
  }

  static Future<void> addToSyncQueue(Record record) async {
    final prefs = await SharedPreferences.getInstance();
    final existingQueue = await getSyncQueue();
    
    existingQueue.add(record);
    
    final queueJson = existingQueue.map((r) => r.toJson()).toList();
    await prefs.setString(_syncQueueKey, jsonEncode(queueJson));
  }

  static Future<List<Record>> getSyncQueue() async {
    final prefs = await SharedPreferences.getInstance();
    final queueString = prefs.getString(_syncQueueKey);
    
    if (queueString == null) return [];
    
    final queueJson = jsonDecode(queueString) as List;
    return queueJson.map((json) => Record.fromJson(json)).toList();
  }

  static Future<void> clearSyncQueue() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_syncQueueKey);
  }

  static Future<void> removeFromSyncQueue(String recordId) async {
    final prefs = await SharedPreferences.getInstance();
    final queue = await getSyncQueue();
    
    queue.removeWhere((record) => record.id == recordId);
    
    final queueJson = queue.map((r) => r.toJson()).toList();
    await prefs.setString(_syncQueueKey, jsonEncode(queueJson));
  }

  static Future<void> clearOfflineRecords() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_offlineRecordsKey);
  }

  static Future<int> getOfflineRecordCount() async {
    final records = await getOfflineRecords();
    return records.length;
  }

  static Future<int> getSyncQueueCount() async {
    final queue = await getSyncQueue();
    return queue.length;
  }
}
