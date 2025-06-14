import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:go_router/go_router.dart';
import '../services/auth_service.dart';


class ModuleSelectionScreen extends StatelessWidget {
  const ModuleSelectionScreen({super.key});

  final List<Map<String, dynamic>> modules = const [
    {
      'name': 'Milling',
      'icon': Icons.precision_manufacturing,
      'description': 'Ore processing and milling operations',
      'requiredRole': 'operator'
    },
    {
      'name': 'Extraction',
      'icon': Icons.build_circle,
      'description': 'Mineral extraction processes',
      'requiredRole': 'operator'
    },
    {
      'name': 'Blasting',
      'icon': Icons.flash_on,
      'description': 'Controlled blasting operations',
      'requiredRole': 'manager'
    },
    {
      'name': 'Ore Movement',
      'icon': Icons.local_shipping,
      'description': 'Transportation and logistics',
      'requiredRole': 'operator'
    },
    {
      'name': 'Gold Refining',
      'icon': Icons.diamond,
      'description': 'Gold purification processes',
      'requiredRole': 'supervisor'
    },
    {
      'name': 'Materials & Assets',
      'icon': Icons.inventory,
      'description': 'Equipment and material management',
      'requiredRole': 'operator'
    }
  ];

  bool _canAccessModule(String requiredRole, String userRole) {
    const roleHierarchy = {
      'operator': 1,
      'manager': 2,
      'supervisor': 3,
      'admin': 4
    };
    
    return (roleHierarchy[userRole] ?? 0) >= (roleHierarchy[requiredRole] ?? 0);
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<AuthService>(
      builder: (context, authService, child) {
        final userRole = authService.currentUser?.role ?? 'operator';
        
        return Scaffold(
          appBar: AppBar(
            title: const Text('Select Module'),
            backgroundColor: Theme.of(context).colorScheme.inversePrimary,
          ),
          body: Padding(
            padding: const EdgeInsets.all(16.0),
            child: GridView.builder(
              gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: 2,
                crossAxisSpacing: 16,
                mainAxisSpacing: 16,
                childAspectRatio: 1.2,
              ),
              itemCount: modules.length,
              itemBuilder: (context, index) {
                final module = modules[index];
                final canAccess = _canAccessModule(module['requiredRole'], userRole);
                
                return Card(
                  elevation: canAccess ? 4 : 1,
                  child: InkWell(
                    onTap: canAccess ? () {
                      context.push('/module/${module['name']}');
                    } : null,
                    child: Padding(
                      padding: const EdgeInsets.all(16.0),
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(
                            module['icon'],
                            size: 48,
                            color: canAccess 
                              ? Theme.of(context).primaryColor
                              : Colors.grey,
                          ),
                          const SizedBox(height: 8),
                          Text(
                            module['name'],
                            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                              color: canAccess ? null : Colors.grey,
                              fontWeight: FontWeight.bold,
                            ),
                            textAlign: TextAlign.center,
                          ),
                          const SizedBox(height: 4),
                          Text(
                            module['description'],
                            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              color: canAccess ? null : Colors.grey,
                            ),
                            textAlign: TextAlign.center,
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                          ),
                          if (!canAccess) ...[
                            const SizedBox(height: 4),
                            Text(
                              'Requires ${module['requiredRole']} access',
                              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                color: Colors.red,
                                fontSize: 10,
                              ),
                              textAlign: TextAlign.center,
                            ),
                          ],
                        ],
                      ),
                    ),
                  ),
                );
              },
            ),
          ),
        );
      },
    );
  }
}
