"""Quick test to verify all routes are registered correctly"""
import sys

try:
    # Import the Flask app
    from app import app
    
    # Get all registered routes
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            'endpoint': rule.endpoint,
            'methods': ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'})),
            'path': str(rule)
        })
    
    # Sort by path
    routes.sort(key=lambda x: x['path'])
    
    print("=" * 80)
    print("ROUTE REGISTRATION TEST - SUCCESS")
    print("=" * 80)
    print(f"\nTotal Routes Registered: {len(routes)}\n")
    
    # Group by blueprint
    blueprints = {}
    for route in routes:
        bp = route['endpoint'].split('.')[0] if '.' in route['endpoint'] else 'main'
        if bp not in blueprints:
            blueprints[bp] = []
        blueprints[bp].append(route)
    
    for bp_name, bp_routes in sorted(blueprints.items()):
        print(f"\n{bp_name.upper()} ({len(bp_routes)} routes)")
        print("-" * 40)
        for route in bp_routes[:5]:  # Show first 5 of each blueprint
            print(f"  {route['methods']:20} {route['path']}")
        if len(bp_routes) > 5:
            print(f"  ... and {len(bp_routes) - 5} more routes")
    
    print("\n" + "=" * 80)
    print("✓ All blueprints loaded successfully!")
    print("=" * 80)
    sys.exit(0)
    
except Exception as e:
    print("=" * 80)
    print("ROUTE REGISTRATION TEST - FAILED")
    print("=" * 80)
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
