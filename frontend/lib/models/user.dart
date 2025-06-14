import 'package:json_annotation/json_annotation.dart';

part 'user.g.dart';

@JsonSerializable()
class User {
  final String id;
  final String name;
  final String email;
  final String role;
  @JsonKey(name: 'is_active')
  final bool isActive;
  @JsonKey(name: 'created_at')
  final DateTime? createdAt;

  const  User({
    required this.id,
    required this.name,
    required this.email,
    required this.role,
    required this.isActive,
    this.createdAt,
  });

  factory User.fromJson(Map<String, dynamic> json) => _$UserFromJson(json);
  Map<String, dynamic> toJson() => _$UserToJson(this);

  bool get isOperator => role == 'operator';
  bool get isManager => role == 'manager';
  bool get isSupervisor => role == 'supervisor';
  bool get isAdmin => role == 'admin';
  
  bool get canApproveRecords => isManager || isSupervisor || isAdmin;
  bool get canViewAllUsers => canApproveRecords;
  bool get canRegisterUsers => isAdmin;

  bool canAccessModule(String requiredRole) {
    const roleHierarchy = {
      'operator': 1,
      'manager': 2,
      'supervisor': 3,
      'admin': 4
    };
    
    return (roleHierarchy[role.toLowerCase()] ?? 0) >= (roleHierarchy[requiredRole.toLowerCase()] ?? 0);
  }
}
