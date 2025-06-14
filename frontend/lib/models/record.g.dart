// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'record.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

Record _$RecordFromJson(Map<String, dynamic> json) => Record(
      id: json['id'] as String,
      module: json['module'] as String,
      data: json['data'] as Map<String, dynamic>,
      managerOnDuty: json['manager_on_duty'] as String,
      submittedBy: json['submitted_by'] as String,
      approvalStatus: json['approval_status'] as String,
      approvedBy: json['approved_by'] as String?,
      timestamp: DateTime.parse(json['timestamp'] as String),
      createdAt: json['created_at'] == null
          ? null
          : DateTime.parse(json['created_at'] as String),
      updatedAt: json['updated_at'] == null
          ? null
          : DateTime.parse(json['updated_at'] as String),
      userId: json['user_id'] as String?,
    );

Map<String, dynamic> _$RecordToJson(Record instance) => <String, dynamic>{
      'id': instance.id,
      'module': instance.module,
      'data': instance.data,
      'manager_on_duty': instance.managerOnDuty,
      'submitted_by': instance.submittedBy,
      'approval_status': instance.approvalStatus,
      'approved_by': instance.approvedBy,
      'timestamp': instance.timestamp.toIso8601String(),
      'created_at': instance.createdAt?.toIso8601String(),
      'updated_at': instance.updatedAt?.toIso8601String(),
      'user_id': instance.userId,
    };
