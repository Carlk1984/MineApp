import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:go_router/go_router.dart';
import '../services/auth_service.dart';
import '../services/hive_service.dart';

class DashboardScreen extends StatelessWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Mine KPI Dashboard'),
        actions: [
          Consumer<AuthService>(
            builder: (context, authService, child) {
              return PopupMenuButton(
                child: Padding(
                  padding: const EdgeInsets.all(8.0),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      CircleAvatar(
                        child: Text(
                          authService.currentUser?.name.substring(0, 1).toUpperCase() ?? 'U',
                        ),
                      ),
                      const SizedBox(width: 8),
                      Text(authService.currentUser?.name ?? 'User'),
                    ],
                  ),
                ),
                itemBuilder: (context) => [
                  PopupMenuItem(
                    onTap: () => authService.logout(),
                    child: const Row(
                      children: [
                        Icon(Icons.logout),
                        SizedBox(width: 8),
                        Text('Logout'),
                      ],
                    ),
                  ),
                ],
              );
            },
          ),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Consumer<AuthService>(
              builder: (context, authService, child) {
                final user = authService.currentUser;
                return Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Welcome, ${user?.name ?? 'User'}!',
                          style: Theme.of(context).textTheme.headlineSmall,
                        ),
                        const SizedBox(height: 8),
                        Text('Role: ${user?.role.toUpperCase() ?? 'UNKNOWN'}'),
                        Text('Email: ${user?.email ?? 'unknown@example.com'}'),
                      ],
                    ),
                  ),
                );
              },
            ),
            const SizedBox(height: 24),
            Text(
              'Quick Actions',
              style: Theme.of(context).textTheme.headlineSmall,
            ),
            const SizedBox(height: 16),
            Expanded(
              child: GridView.count(
                crossAxisCount: 2,
                crossAxisSpacing: 16,
                mainAxisSpacing: 16,
                children: [
                  _buildActionCard(
                    context,
                    'Modules',
                    Icons.dashboard,
                    'Access mining modules',
                    () => context.go('/modules'),
                  ),
                  _buildActionCard(
                    context,
                    'Records',
                    Icons.assignment,
                    'View and manage KPI records',
                    () => context.go('/records'),
                  ),
                  Consumer<AuthService>(
                    builder: (context, authService, child) {
                      final canViewUsers = authService.currentUser?.canViewAllUsers ?? false;
                      return _buildActionCard(
                        context,
                        'Users',
                        Icons.people,
                        canViewUsers ? 'Manage users' : 'View profile',
                        canViewUsers ? () => context.go('/users') : null,
                      );
                    },
                  ),
                  Consumer<HiveService>(
                    builder: (context, hiveService, child) {
                      return FutureBuilder<int>(
                        future: hiveService.getConflictCount(),
                        builder: (context, snapshot) {
                          final conflictCount = snapshot.data ?? 0;
                          return _buildConflictCard(
                            context,
                            'Sync Conflicts',
                            Icons.sync_problem,
                            conflictCount > 0 
                                ? '$conflictCount conflicts need attention'
                                : 'No conflicts to resolve',
                            () => context.go('/conflicts'),
                            conflictCount,
                          );
                        },
                      );
                    },
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildActionCard(
    BuildContext context,
    String title,
    IconData icon,
    String description,
    VoidCallback? onTap,
  ) {
    return Card(
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(8),
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                icon,
                size: 48,
                color: onTap != null ? Colors.blue : Colors.grey,
              ),
              const SizedBox(height: 8),
              Text(
                title,
                style: const TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                description,
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 12,
                  color: Colors.grey[600],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildConflictCard(
    BuildContext context,
    String title,
    IconData icon,
    String description,
    VoidCallback? onTap,
    int conflictCount,
  ) {
    return Card(
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(8),
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Stack(
            children: [
              Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    icon,
                    size: 48,
                    color: conflictCount > 0 ? Colors.orange : Colors.grey,
                  ),
                  const SizedBox(height: 8),
                  Text(
                    title,
                    style: const TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    description,
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 12,
                      color: Colors.grey[600],
                    ),
                  ),
                ],
              ),
              if (conflictCount > 0)
                Positioned(
                  top: 0,
                  right: 0,
                  child: Container(
                    padding: const EdgeInsets.all(6),
                    decoration: const BoxDecoration(
                      color: Colors.red,
                      shape: BoxShape.circle,
                    ),
                    child: Text(
                      conflictCount.toString(),
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}
