import 'package:flutter/foundation.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'dart:convert';
import '../models/record.dart';
import 'api_service.dart';
import 'auth_service.dart';

enum ConflictResolutionStrategy {
  latestTimestampWins,
  manualReview,
  keepBoth
}

class SyncConflict {
  final String localRecordId;
  final Record localRecord;
  final Record? serverRecord;
  final DateTime conflictDetectedAt;
  final String conflictReason;

  SyncConflict({
    required this.localRecordId,
    required this.localRecord,
    this.serverRecord,
    required this.conflictDetectedAt,
    required this.conflictReason,
  });

  Map<String, dynamic> toJson() => {
    'localRecordId': localRecordId,
    'localRecord': localRecord.toJson(),
    'serverRecord': serverRecord?.toJson(),
    'conflictDetectedAt': conflictDetectedAt.toIso8601String(),
    'conflictReason': conflictReason,
  };

  factory SyncConflict.fromJson(Map<String, dynamic> json) => SyncConflict(
    localRecordId: json['localRecordId'],
    localRecord: Record.fromJson(json['localRecord']),
    serverRecord: json['serverRecord'] != null ? Record.fromJson(json['serverRecord']) : null,
    conflictDetectedAt: DateTime.parse(json['conflictDetectedAt']),
    conflictReason: json['conflictReason'],
  );
}

class SyncResult {
  final int totalRecords;
  final int successfulSyncs;
  final int conflicts;
  final int errors;
  final List<SyncConflict> conflictList;
  final List<String> errorMessages;

  SyncResult({
    required this.totalRecords,
    required this.successfulSyncs,
    required this.conflicts,
    required this.errors,
    required this.conflictList,
    required this.errorMessages,
  });
}

class HiveService {
  static const String _offlineRecordsBox = 'offline_records';
  static const String _syncQueueBox = 'sync_queue';
  static const String _conflictsBox = 'sync_conflicts';
  static const String _syncMetadataBox = 'sync_metadata';
  
  late Box<String> _offlineRecordsBoxInstance;
  late Box<String> _syncQueueBoxInstance;
  late Box<String> _conflictsBoxInstance;
  late Box<String> _syncMetadataBoxInstance;
  
  final ApiService _apiService = ApiService();
  final Connectivity _connectivity = Connectivity();
  
  ConflictResolutionStrategy _conflictStrategy = ConflictResolutionStrategy.latestTimestampWins;

  Future<void> initialize() async {
    await Hive.initFlutter();
    _offlineRecordsBoxInstance = await Hive.openBox<String>(_offlineRecordsBox);
    _syncQueueBoxInstance = await Hive.openBox<String>(_syncQueueBox);
    _conflictsBoxInstance = await Hive.openBox<String>(_conflictsBox);
    _syncMetadataBoxInstance = await Hive.openBox<String>(_syncMetadataBox);
  }

  void setConflictResolutionStrategy(ConflictResolutionStrategy strategy) {
    _conflictStrategy = strategy;
  }

  ConflictResolutionStrategy get conflictResolutionStrategy => _conflictStrategy;

  Future<void> saveOfflineRecord(Record record) async {
    final recordWithMetadata = record.copyWith(
      createdAt: record.createdAt ?? DateTime.now(),
      updatedAt: DateTime.now(),
    );
    
    final recordJson = jsonEncode(recordWithMetadata.toJson());
    final timestamp = DateTime.now().millisecondsSinceEpoch.toString();
    
    await _offlineRecordsBoxInstance.put(timestamp, recordJson);
    await _syncQueueBoxInstance.put(timestamp, recordJson);
    
    await _syncMetadataBoxInstance.put('${timestamp}_created', DateTime.now().toIso8601String());
    await _syncMetadataBoxInstance.put('${timestamp}_device_id', 'local_device');
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

  Future<SyncResult> syncOfflineRecords(AuthService authService) async {
    if (!await isOnline()) {
      debugPrint('Device is offline, cannot sync');
      return SyncResult(
        totalRecords: 0,
        successfulSyncs: 0,
        conflicts: 0,
        errors: 1,
        conflictList: [],
        errorMessages: ['Device is offline'],
      );
    }

    final authToken = authService.getAuthHeader();
    if (authToken == null) {
      debugPrint('No auth token available for sync');
      return SyncResult(
        totalRecords: 0,
        successfulSyncs: 0,
        conflicts: 0,
        errors: 1,
        conflictList: [],
        errorMessages: ['No authentication token available'],
      );
    }

    final syncKeys = _syncQueueBoxInstance.keys.toList();
    final successfulSyncs = <String>[];
    final conflicts = <SyncConflict>[];
    final errors = <String>[];

    for (final key in syncKeys) {
      final recordJson = _syncQueueBoxInstance.get(key);
      if (recordJson != null) {
        try {
          final recordMap = jsonDecode(recordJson) as Map<String, dynamic>;
          final localRecord = Record.fromJson(recordMap);
          
          final conflictResult = await _handleSyncConflict(
            key.toString(),
            localRecord,
            authToken.replaceFirst('Bearer ', ''),
          );
          
          if (conflictResult.hasConflict) {
            conflicts.add(conflictResult.conflict!);
            if (_conflictStrategy == ConflictResolutionStrategy.manualReview) {
              await _storeConflictForReview(conflictResult.conflict!);
              continue;
            }
          }
          
          if (conflictResult.shouldSync) {
            await _apiService.createRecord(
              authToken.replaceFirst('Bearer ', ''),
              conflictResult.recordToSync!.toJson(),
            );
            successfulSyncs.add(key.toString());
            debugPrint('Successfully synced record: $key');
          }
          
        } catch (e) {
          errors.add('Failed to sync record $key: $e');
          debugPrint('Failed to sync record $key: $e');
        }
      }
    }

    for (final key in successfulSyncs) {
      await _syncQueueBoxInstance.delete(key);
    }

    final result = SyncResult(
      totalRecords: syncKeys.length,
      successfulSyncs: successfulSyncs.length,
      conflicts: conflicts.length,
      errors: errors.length,
      conflictList: conflicts,
      errorMessages: errors,
    );

    debugPrint('Sync completed: ${result.successfulSyncs}/${result.totalRecords} records synced, ${result.conflicts} conflicts, ${result.errors} errors');
    return result;
  }

  Future<_ConflictResolutionResult> _handleSyncConflict(
    String localRecordId,
    Record localRecord,
    String authToken,
  ) async {
    try {
      final existingRecords = await _apiService.getRecords(authToken);
      
      final potentialConflict = existingRecords.firstWhere(
        (serverRecord) => _recordsConflict(localRecord, serverRecord),
        orElse: () => throw StateError('No conflict found'),
      );
      
      final conflict = SyncConflict(
        localRecordId: localRecordId,
        localRecord: localRecord,
        serverRecord: potentialConflict,
        conflictDetectedAt: DateTime.now(),
        conflictReason: 'Similar record found on server',
      );
      
      switch (_conflictStrategy) {
        case ConflictResolutionStrategy.latestTimestampWins:
          final localTime = localRecord.updatedAt ?? localRecord.createdAt ?? DateTime.now();
          final serverTime = potentialConflict.updatedAt ?? potentialConflict.createdAt ?? DateTime.now();
          
          if (localTime.isAfter(serverTime)) {
            return _ConflictResolutionResult(
              hasConflict: true,
              conflict: conflict,
              shouldSync: true,
              recordToSync: localRecord,
            );
          } else {
            return _ConflictResolutionResult(
              hasConflict: true,
              conflict: conflict,
              shouldSync: false,
            );
          }
          
        case ConflictResolutionStrategy.manualReview:
          return _ConflictResolutionResult(
            hasConflict: true,
            conflict: conflict,
            shouldSync: false,
          );
          
        case ConflictResolutionStrategy.keepBoth:
          final modifiedRecord = localRecord.copyWith(
            data: {
              ...localRecord.data,
              'conflict_resolution': 'keep_both',
              'original_timestamp': localRecord.createdAt?.toIso8601String(),
            },
          );
          return _ConflictResolutionResult(
            hasConflict: true,
            conflict: conflict,
            shouldSync: true,
            recordToSync: modifiedRecord,
          );
      }
    } catch (e) {
      return _ConflictResolutionResult(
        hasConflict: false,
        shouldSync: true,
        recordToSync: localRecord,
      );
    }
  }

  bool _recordsConflict(Record local, Record server) {
    if (local.module != server.module) return false;
    
    final localDate = local.createdAt?.toIso8601String().substring(0, 10);
    final serverDate = server.createdAt?.toIso8601String().substring(0, 10);
    
    if (localDate != serverDate) return false;
    
    if (local.userId == server.userId) return true;
    
    final timeDifference = (local.createdAt ?? DateTime.now())
        .difference(server.createdAt ?? DateTime.now())
        .abs();
    
    return timeDifference.inMinutes < 30;
  }

  Future<void> _storeConflictForReview(SyncConflict conflict) async {
    final conflictJson = jsonEncode(conflict.toJson());
    final conflictId = '${conflict.localRecordId}_${DateTime.now().millisecondsSinceEpoch}';
    await _conflictsBoxInstance.put(conflictId, conflictJson);
  }

  Future<List<SyncConflict>> getPendingConflicts() async {
    final conflicts = <SyncConflict>[];
    for (final key in _conflictsBoxInstance.keys) {
      final conflictJson = _conflictsBoxInstance.get(key);
      if (conflictJson != null) {
        try {
          final conflictMap = jsonDecode(conflictJson) as Map<String, dynamic>;
          conflicts.add(SyncConflict.fromJson(conflictMap));
        } catch (e) {
          debugPrint('Error parsing conflict: $e');
        }
      }
    }
    return conflicts;
  }

  Future<void> resolveConflict(String conflictId, Record resolvedRecord) async {
    await _conflictsBoxInstance.delete(conflictId);
    
    final recordJson = jsonEncode(resolvedRecord.toJson());
    final timestamp = DateTime.now().millisecondsSinceEpoch.toString();
    await _syncQueueBoxInstance.put('resolved_$timestamp', recordJson);
  }

  Future<void> dismissConflict(String conflictId) async {
    await _conflictsBoxInstance.delete(conflictId);
  }

  Future<int> getConflictCount() async {
    return _conflictsBoxInstance.length;
  }

  Future<void> clearOfflineRecords() async {
    await _offlineRecordsBoxInstance.clear();
  }

  Future<void> clearSyncQueue() async {
    await _syncQueueBoxInstance.clear();
  }

  Future<void> clearConflicts() async {
    await _conflictsBoxInstance.clear();
  }

  Future<void> clearSyncMetadata() async {
    await _syncMetadataBoxInstance.clear();
  }

  Stream<ConnectivityResult> get connectivityStream => _connectivity.onConnectivityChanged;

  void dispose() {
    _offlineRecordsBoxInstance.close();
    _syncQueueBoxInstance.close();
    _conflictsBoxInstance.close();
    _syncMetadataBoxInstance.close();
  }
}

class _ConflictResolutionResult {
  final bool hasConflict;
  final SyncConflict? conflict;
  final bool shouldSync;
  final Record? recordToSync;

  _ConflictResolutionResult({
    required this.hasConflict,
    this.conflict,
    required this.shouldSync,
    this.recordToSync,
  });
}
