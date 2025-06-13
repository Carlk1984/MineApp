import 'package:json_annotation/json_annotation.dart';

part 'record.g.dart';

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

  const Record({
    required this.id,
    required this.module,
    required this.data,
    required this.managerOnDuty,
    required this.submittedBy,
    required this.approvalStatus,
    this.approvedBy,
    required this.timestamp,
  });

  factory Record.fromJson(Map<String, dynamic> json) => _$RecordFromJson(json);
  Map<String, dynamic> toJson() => _$RecordToJson(this);

  bool get isPending => approvalStatus == 'pending';
  bool get isApproved => approvalStatus == 'approved';
  bool get isRejected => approvalStatus == 'rejected';
}
