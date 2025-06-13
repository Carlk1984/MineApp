import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:go_router/go_router.dart';
import 'services/auth_service.dart';
import 'services/api_service.dart';
import 'screens/login_screen.dart';
import 'screens/dashboard_screen.dart';
import 'screens/records_screen.dart';
import 'screens/users_screen.dart';

void main() {
  runApp(const MineKpiApp());
}

class MineKpiApp extends StatelessWidget {
  const MineKpiApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthService()),
        ChangeNotifierProvider(create: (_) => ApiService()),
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
        final isLoginRoute = state.location == '/login';

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
      ],
    );
  }
}
