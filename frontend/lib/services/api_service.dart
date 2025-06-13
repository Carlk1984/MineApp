import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import '../models/record.dart';
import '../models/user.dart';

class ApiService extends ChangeNotifier {
  static const String baseUrl = 'http://localhost:8000';
  
  Future<List<Record>> getRecords(String authToken) async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/records'),
        headers: {
          'Authorization': 'Bearer $authToken',
          'Content-Type': 'application/json',
        },
      );

      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(response.body);
        return data.map((json) => Record.fromJson(json)).toList();
      }
      throw Exception('Failed to load records');
    } catch (e) {
      debugPrint('Get records error: $e');
      rethrow;
    }
  }

  Future<Record> createRecord(String authToken, Map<String, dynamic> recordData) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/record'),
        headers: {
          'Authorization': 'Bearer $authToken',
          'Content-Type': 'application/json',
        },
        body: jsonEncode(recordData),
      );

      if (response.statusCode == 200) {
        return Record.fromJson(jsonDecode(response.body));
      }
      throw Exception('Failed to create record');
    } catch (e) {
      debugPrint('Create record error: $e');
      rethrow;
    }
  }

  Future<List<User>> getUsers(String authToken) async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/users'),
        headers: {
          'Authorization': 'Bearer $authToken',
          'Content-Type': 'application/json',
        },
      );

      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(response.body);
        return data.map((json) => User.fromJson(json)).toList();
      }
      throw Exception('Failed to load users');
    } catch (e) {
      debugPrint('Get users error: $e');
      rethrow;
    }
  }

  Future<void> approveRecord(String authToken, String recordId) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/record/$recordId/approve'),
        headers: {
          'Authorization': 'Bearer $authToken',
          'Content-Type': 'application/json',
        },
      );

      if (response.statusCode != 200) {
        throw Exception('Failed to approve record');
      }
    } catch (e) {
      debugPrint('Approve record error: $e');
      rethrow;
    }
  }

  Future<void> rejectRecord(String authToken, String recordId) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/record/$recordId/reject'),
        headers: {
          'Authorization': 'Bearer $authToken',
          'Content-Type': 'application/json',
        },
      );

      if (response.statusCode != 200) {
        throw Exception('Failed to reject record');
      }
    } catch (e) {
      debugPrint('Reject record error: $e');
      rethrow;
    }
  }
}
