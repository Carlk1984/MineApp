import 'package:flutter/foundation.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'dart:convert';
import '../models/record.dart';
import 'api_service.dart';
import 'auth_service.dart';

class HiveService {
  static const String _offlineRecordsBox = 'offline_records';
  static const String _syncQueueBox = 'sync_queue';
  
  late Box<String> _offlineRecordsBoxInstance;
  late Box<String> _syncQueueBoxInstance;
  
  final ApiService _apiService = ApiService();
  final Connectivity _connectivity = Connectivity();

  Future<void> initialize() async {
    await Hive.initFlutter();
    _offlineRecordsBoxInstance = await Hive.openBox<String>(_offlineRecordsBox);
    _syncQueueBoxInstance = await Hive.openBox<String>(_syncQueueBox);
  }

  Future<void> saveOfflineRecord(Record record) async {
    final recordJson = jsonEncode(record.toJson());
    final timestamp = DateTime.now().millisecondsSinceEpoch.toString();
    await _offlineRecordsBoxInstance.put(timestamp, recordJson);
    await _syncQueueBoxInstance.put(timestamp, recordJson);
  }

  Future<List<Record>> getOfflineRecords() async {
    final records = <Record>[];
    for (final key in _offlineRecordsBoxInstance.keys) {
      final recordJson = _offlineRecordsBoxInstance.get(key);
      if (recordJson != null) {
        try {
          final recordMap = jsonDecode(recordJson) as Map<String, dynamic>;
          records.add(Record.fromJson(recordMap));
        } catch (e) {
          debugPrint('Error parsing offline record: $e');
        }
      }
    }
    return records;
  }

  Future<int> getOfflineRecordCount() async {
    return _offlineRecordsBoxInstance.length;
  }

  Future<int> getSyncQueueCount() async {
    return _syncQueueBoxInstance.length;
  }

  Future<bool> isOnline() async {
    final connectivityResult = await _connectivity.checkConnectivity();
    return connectivityResult != ConnectivityResult.none;
  }

  Future<void> syncOfflineRecords(AuthService authService) async {
    if (!await isOnline()) {
      debugPrint('Device is offline, cannot sync');
      return;
    }

    final authToken = authService.getAuthHeader();
    if (authToken == null) {
      debugPrint('No auth token available for sync');
      return;
    }

    final syncKeys = _syncQueueBoxInstance.keys.toList();
    final successfulSyncs = <String>[];

    for (final key in syncKeys) {
      final recordJson = _syncQueueBoxInstance.get(key);
      if (recordJson != null) {
        try {
          final recordMap = jsonDecode(recordJson) as Map<String, dynamic>;
          final record = Record.fromJson(recordMap);
          
          await _apiService.createRecord(
            authToken.replaceFirst('Bearer ', ''),
            record.toJson(),
          );
          
          successfulSyncs.add(key.toString());
          debugPrint('Successfully synced record: $key');
        } catch (e) {
          debugPrint('Failed to sync record $key: $e');
        }
      }
    }

    for (final key in successfulSyncs) {
      await _syncQueueBoxInstance.delete(key);
    }

    debugPrint('Sync completed: ${successfulSyncs.length}/${syncKeys.length} records synced');
  }

  Future<void> clearOfflineRecords() async {
    await _offlineRecordsBoxInstance.clear();
  }

  Future<void> clearSyncQueue() async {
    await _syncQueueBoxInstance.clear();
  }

  Stream<ConnectivityResult> get connectivityStream => _connectivity.onConnectivityChanged;

  void dispose() {
    _offlineRecordsBoxInstance.close();
    _syncQueueBoxInstance.close();
  }
}
