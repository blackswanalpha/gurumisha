#!/usr/bin/env python3
"""
Test script to verify the admin sidebar improvements
"""

import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gurumisha_project.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()

def test_sidebar_improvements():
    """Test that the sidebar improvements are working"""
    
    print("Testing Admin Sidebar Improvements:")
    print("=" * 50)
    
    # Create a test client
    client = Client()
    
    # Create an admin user
    admin_user = User.objects.filter(role='admin').first()
    if not admin_user:
        admin_user = User.objects.create_user(
            username='testadmin',
            email='admin@test.com',
            password='testpass123',
            role='admin'
        )
    
    # Login as admin
    client.force_login(admin_user)
    
    # Test dashboard page loads with new sidebar
    response = client.get(reverse('core:dashboard'))
    
    if response.status_code == 200:
        content = response.content.decode('utf-8')
        
        # Check for new sidebar structure
        improvements = [
            ('Modern Navigation Structure', 'nav-section' in content),
            ('Section Headers', 'section-header' in content),
            ('Navigation Links', 'nav-link' in content),
            ('Navigation Icons', 'nav-link-icon' in content),
            ('Active State Pills', 'nav-link-pill' in content),
            ('Main Navigation Cards', 'main-nav-card' in content),
            ('Navigation Badges', 'nav-badge' in content),
            ('Improved Icons', 'fas fa-chart-pie' in content),  # Dashboard icon
            ('Import Section', 'fas fa-shipping-fast' in content),  # Import section icon
            ('User Management', 'fas fa-users-cog' in content),  # User management icon
            ('Inventory Section', 'fas fa-boxes' in content),  # Inventory icon
            ('Communication', 'fas fa-comments' in content),  # Communication icon
            ('Content & Settings', 'fas fa-cogs' in content),  # Settings icon
        ]
        
        print("Sidebar Improvement Checks:")
        print("-" * 30)
        
        passed = 0
        total = len(improvements)
        
        for improvement, check in improvements:
            status = "✅ PASS" if check else "❌ FAIL"
            print(f"{improvement}: {status}")
            if check:
                passed += 1
        
        print("-" * 30)
        print(f"Results: {passed}/{total} improvements verified")
        
        # Check for CSS classes
        css_classes = [
            'sidebar-nav',
            'nav-section',
            'section-header-content',
            'nav-link-content',
            'nav-link-left',
            'nav-link-right',
            'main-nav-card',
        ]
        
        print("\nCSS Class Structure:")
        print("-" * 20)
        
        css_passed = 0
        for css_class in css_classes:
            found = css_class in content
            status = "✅ FOUND" if found else "❌ MISSING"
            print(f"{css_class}: {status}")
            if found:
                css_passed += 1
        
        print("-" * 20)
        print(f"CSS Classes: {css_passed}/{len(css_classes)} found")
        
        # Overall assessment
        overall_score = (passed + css_passed) / (total + len(css_classes)) * 100
        
        print("\n" + "=" * 50)
        print("OVERALL ASSESSMENT:")
        print(f"Sidebar Improvements: {overall_score:.1f}% Complete")
        
        if overall_score >= 90:
            print("🎉 EXCELLENT: All major improvements implemented!")
            return True
        elif overall_score >= 75:
            print("✅ GOOD: Most improvements implemented successfully!")
            return True
        elif overall_score >= 50:
            print("⚠️  PARTIAL: Some improvements need attention!")
            return False
        else:
            print("❌ NEEDS WORK: Major improvements missing!")
            return False
            
    else:
        print(f"❌ Dashboard page failed to load: {response.status_code}")
        return False

if __name__ == '__main__':
    print("Gurumisha Admin Sidebar Improvement Test")
    print("=" * 50)
    
    success = test_sidebar_improvements()
    
    if success:
        print("\n🎉 Sidebar improvements test PASSED!")
        sys.exit(0)
    else:
        print("\n⚠️  Sidebar improvements test needs attention!")
        sys.exit(1)
