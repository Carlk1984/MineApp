import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:go_router/go_router.dart';
import 'services/auth_service.dart';
import 'services/api_service.dart';
import 'services/hive_service.dart';
import 'screens/login_screen.dart';
import 'screens/dashboard_screen.dart';
import 'screens/records_screen.dart';
import 'screens/users_screen.dart';
import 'screens/module_selection_screen.dart';
import 'screens/module_form_screen.dart';
import 'screens/conflict_resolution_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  final hiveService = HiveService();
  await hiveService.initialize();
  
  runApp(MineKpiApp(hiveService: hiveService));
}

class MineKpiApp extends StatelessWidget {
  final HiveService hiveService;
  
  const MineKpiApp({super.key, required this.hiveService});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthService()),
        ChangeNotifierProvider(create: (_) => ApiService()),
        Provider.value(value: hiveService),
      ],
      child: Consumer<AuthService>(
        builder: (context, authService, child) {
          return MaterialApp.router(
            title: 'Mine KPI Tracker',
            theme: ThemeData(
              primarySwatch: Colors.blue,
              useMaterial3: true,
            ),
            routerConfig: _createRouter(authService),
          );
        },
      ),
    );
  }

  GoRouter _createRouter(AuthService authService) {
    return GoRouter(
      initialLocation: authService.isAuthenticated ? '/dashboard' : '/login',
      redirect: (context, state) {
        final isAuthenticated = authService.isAuthenticated;
        final isLoginRoute = state.uri.toString() == '/login';

        if (!isAuthenticated && !isLoginRoute) {
          return '/login';
        }
        if (isAuthenticated && isLoginRoute) {
          return '/dashboard';
        }
        return null;
      },
      routes: [
        GoRoute(
          path: '/login',
          builder: (context, state) => const LoginScreen(),
        ),
        GoRoute(
          path: '/dashboard',
          builder: (context, state) => const DashboardScreen(),
        ),
        GoRoute(
          path: '/records',
          builder: (context, state) => const RecordsScreen(),
        ),
        GoRoute(
          path: '/users',
          builder: (context, state) => const UsersScreen(),
        ),
        GoRoute(
          path: '/modules',
          builder: (context, state) => const ModuleSelectionScreen(),
        ),
        GoRoute(
          path: '/module/:moduleName',
          builder: (context, state) {
            final moduleName = state.pathParameters['moduleName']!;
            return ModuleFormScreen(moduleName: moduleName);
          },
        ),
        GoRoute(
          path: '/conflicts',
          builder: (context, state) => const ConflictResolutionScreen(),
        ),
      ],
    );
  }
}
