import 'package:json_annotation/json_annotation.dart';

part 'record.g.dart';

@JsonSerializable()
class LocationData {
  final double latitude;
  final double longitude;
  final double? accuracy;
  final DateTime timestamp;

  const LocationData({
    required this.latitude,
    required this.longitude,
    this.accuracy,
    required this.timestamp,
  });

  factory LocationData.fromJson(Map<String, dynamic> json) => _$LocationDataFromJson(json);
  Map<String, dynamic> toJson() => _$LocationDataToJson(this);
}

@JsonSerializable()
class Record {
  final String id;
  final String module;
  final Map<String, dynamic> data;
  @JsonKey(name: 'manager_on_duty')
  final String managerOnDuty;
  @JsonKey(name: 'submitted_by')
  final String submittedBy;
  @JsonKey(name: 'approval_status')
  final String approvalStatus;
  @JsonKey(name: 'approved_by')
  final String? approvedBy;
  final DateTime timestamp;
  @JsonKey(name: 'created_at')
  final DateTime? createdAt;
  @JsonKey(name: 'updated_at')
  final DateTime? updatedAt;
  @JsonKey(name: 'user_id')
  final String? userId;
  @JsonKey(name: 'location_data')
  final LocationData? locationData;
  @JsonKey(name: 'photos')
  final List<String>? photos;
  @JsonKey(name: 'signature')
  final String? signature;

  const Record({
    required this.id,
    required this.module,
    required this.data,
    required this.managerOnDuty,
    required this.submittedBy,
    required this.approvalStatus,
    this.approvedBy,
    required this.timestamp,
    this.createdAt,
    this.updatedAt,
    this.userId,
    this.locationData,
    this.photos,
    this.signature,
  });

  factory Record.fromJson(Map<String, dynamic> json) => _$RecordFromJson(json);
  Map<String, dynamic> toJson() => _$RecordToJson(this);

  Record copyWith({
    String? id,
    String? module,
    Map<String, dynamic>? data,
    String? managerOnDuty,
    String? submittedBy,
    String? approvalStatus,
    String? approvedBy,
    DateTime? timestamp,
    DateTime? createdAt,
    DateTime? updatedAt,
    String? userId,
    LocationData? locationData,
    List<String>? photos,
    String? signature,
  }) {
    return Record(
      id: id ?? this.id,
      module: module ?? this.module,
      data: data ?? this.data,
      managerOnDuty: managerOnDuty ?? this.managerOnDuty,
      submittedBy: submittedBy ?? this.submittedBy,
      approvalStatus: approvalStatus ?? this.approvalStatus,
      approvedBy: approvedBy ?? this.approvedBy,
      timestamp: timestamp ?? this.timestamp,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
      userId: userId ?? this.userId,
      locationData: locationData ?? this.locationData,
      photos: photos ?? this.photos,
      signature: signature ?? this.signature,
    );
  }

  bool get isPending => approvalStatus == 'pending';
  bool get isApproved => approvalStatus == 'approved';
  bool get isRejected => approvalStatus == 'rejected';
}
