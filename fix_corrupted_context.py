#!/usr/bin/env python3
"""
Database repair script for fixing corrupted user context entries.

This script fixes the data corruption issue where user names were truncated
during conscious ingestion, specifically "Harshal" -> "is".
"""

import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path


def get_correct_user_info(db_path: str) -> dict:
    """Extract correct user information from long-term memory."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    try:
        cursor = conn.execute("""
            SELECT searchable_content, summary FROM long_term_memory 
            WHERE (searchable_content LIKE '%name is%' OR 
                   searchable_content LIKE '%User''s name%' OR
                   searchable_content LIKE '%work%' OR 
                   searchable_content LIKE '%company%')
            ORDER BY created_at DESC
        """)
        
        user_info = {}
        
        for row in cursor.fetchall():
            content = row['searchable_content'].lower()
            original_content = row['searchable_content']
            
            # Extract name
            if 'name is' in content and 'user' in content:
                # Parse "User's name is Harshal" 
                if 'harshal' in content:
                    user_info['name'] = 'Harshal'
                    print(f"Found correct name in: {original_content}")
            
            # Extract company information
            if 'gibson' in content and ('work' in content or 'company' in content):
                user_info['company'] = 'Gibson AI'
                print(f"Found company info in: {original_content}")
                
        return user_info
        
    finally:
        conn.close()


def fix_corrupted_context_entries(db_path: str, correct_info: dict):
    """Fix corrupted permanent context entries in short-term memory."""
    conn = sqlite3.connect(db_path)
    
    try:
        # Get all permanent context entries
        cursor = conn.execute("""
            SELECT memory_id, processed_data FROM short_term_memory 
            WHERE is_permanent_context = 1 AND category_primary = 'user_context'
        """)
        
        corrupted_entries = []
        for row in cursor.fetchall():
            memory_id = row[0]
            processed_data = json.loads(row[1])
            
            # Check if this entry has corrupted name
            profile = processed_data.get('profile', {})
            current_name = profile.get('name')
            
            if current_name == 'is' or (current_name and len(current_name) < 3):
                corrupted_entries.append((memory_id, processed_data))
                print(f"Found corrupted entry {memory_id} with name: '{current_name}'")
        
        # Fix each corrupted entry
        for memory_id, processed_data in corrupted_entries:
            profile = processed_data['profile']
            
            # Update with correct information
            if 'name' in correct_info:
                old_name = profile.get('name')
                profile['name'] = correct_info['name']
                print(f"Fixed name: '{old_name}' -> '{correct_info['name']}'")
            
            if 'company' in correct_info:
                profile['company'] = correct_info['company'] 
                print(f"Added company: '{correct_info['company']}'")
                
            # Update timestamp and version
            profile['last_updated'] = datetime.now().isoformat()
            profile['version'] = profile.get('version', 1) + 1
            
            # Update the summary to reflect correct name
            corrected_summary = f"Permanent user context profile"
            corrected_searchable = f"User context: {correct_info.get('name', 'user')}"
            
            # Update database
            conn.execute("""
                UPDATE short_term_memory 
                SET processed_data = ?, 
                    summary = ?,
                    searchable_content = ?
                WHERE memory_id = ?
            """, (
                json.dumps(processed_data),
                corrected_summary, 
                corrected_searchable,
                memory_id
            ))
            
            print(f"Updated database entry {memory_id}")
        
        conn.commit()
        print(f"\nSuccessfully fixed {len(corrupted_entries)} corrupted entries")
        
    except Exception as e:
        conn.rollback()
        print(f"Error fixing entries: {e}")
        raise
    finally:
        conn.close()


def verify_fix(db_path: str):
    """Verify that the fix was successful."""
    conn = sqlite3.connect(db_path)
    
    try:
        cursor = conn.execute("""
            SELECT processed_data FROM short_term_memory 
            WHERE is_permanent_context = 1 AND category_primary = 'user_context'
        """)
        
        print("\nVerification - Current permanent context entries:")
        for row in cursor.fetchall():
            processed_data = json.loads(row[0])
            profile = processed_data.get('profile', {})
            name = profile.get('name')
            company = profile.get('company')
            print(f"  Name: {name}")
            print(f"  Company: {company}")
            print(f"  Version: {profile.get('version')}")
            print("  ---")
            
    finally:
        conn.close()


def main():
    """Main repair function."""
    if len(sys.argv) < 2:
        print("Usage: python fix_corrupted_context.py <database_path>")
        print("Example: python fix_corrupted_context.py patch-4.db")
        sys.exit(1)
    
    db_path = sys.argv[1]
    
    if not Path(db_path).exists():
        print(f"Database file {db_path} not found!")
        sys.exit(1)
    
    print(f"Analyzing database: {db_path}")
    
    # Step 1: Extract correct user information from long-term memory
    print("\n1. Extracting correct user information from long-term memory...")
    correct_info = get_correct_user_info(db_path)
    
    if not correct_info:
        print("No user information found in long-term memory!")
        sys.exit(1)
        
    print(f"Correct user information found: {correct_info}")
    
    # Step 2: Fix corrupted entries
    print("\n2. Fixing corrupted permanent context entries...")
    fix_corrupted_context_entries(db_path, correct_info)
    
    # Step 3: Verify the fix
    print("\n3. Verifying fix...")
    verify_fix(db_path)
    
    print("\n✅ Database repair completed successfully!")


if __name__ == "__main__":
    main()