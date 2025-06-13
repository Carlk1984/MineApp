import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/auth_service.dart';
import '../services/api_service.dart';
import '../models/user.dart';

class UsersScreen extends StatefulWidget {
  const UsersScreen({super.key});

  @override
  State<UsersScreen> createState() => _UsersScreenState();
}

class _UsersScreenState extends State<UsersScreen> {
  List<User> _users = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadUsers();
  }

  Future<void> _loadUsers() async {
    setState(() => _isLoading = true);
    
    try {
      final authService = context.read<AuthService>();
      final apiService = context.read<ApiService>();
      final authHeader = authService.getAuthHeader();
      
      if (authHeader != null) {
        final users = await apiService.getUsers(authHeader.substring(7));
        setState(() {
          _users = users;
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() => _isLoading = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error loading users: $e')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Users'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadUsers,
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _users.isEmpty
              ? const Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.people, size: 64, color: Colors.grey),
                      SizedBox(height: 16),
                      Text('No users found'),
                    ],
                  ),
                )
              : ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: _users.length,
                  itemBuilder: (context, index) {
                    final user = _users[index];
                    return Card(
                      margin: const EdgeInsets.only(bottom: 8),
                      child: ListTile(
                        leading: CircleAvatar(
                          child: Text(user.name.substring(0, 1).toUpperCase()),
                        ),
                        title: Text(user.name),
                        subtitle: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(user.email),
                            Text('Role: ${user.role.toUpperCase()}'),
                          ],
                        ),
                        trailing: Chip(
                          label: Text(
                            user.isActive ? 'ACTIVE' : 'INACTIVE',
                            style: const TextStyle(fontSize: 12),
                          ),
                          backgroundColor: user.isActive ? Colors.green : Colors.red,
                        ),
                      ),
                    );
                  },
                ),
    );
  }
}
