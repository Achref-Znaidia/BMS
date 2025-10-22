"""
Database service for managing SQLite operations.
"""

import sqlite3
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
from ..config import DatabaseConfig
from ..models import Handover, Requirement, Issue, TestSuite

class DatabaseManager:
    """Database manager for SQLite operations."""
    
    def __init__(self, db_name: str = DatabaseConfig.DB_NAME):
        self.db_name = db_name
        self._create_tables()
        self._insert_sample_data()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        return sqlite3.connect(self.db_name)
    
    def _create_tables(self):
        """Create database tables if they don't exist."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Handovers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS handovers (
                id TEXT PRIMARY KEY,
                from_team TEXT NOT NULL,
                to_team TEXT NOT NULL,
                date TEXT NOT NULL,
                description TEXT,
                documents TEXT,
                status TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        
        # Requirements table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS requirements (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                change_date TEXT,
                priority TEXT,
                status TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        
        # Issues table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS issues (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                type TEXT,
                priority TEXT,
                status TEXT,
                assigned_to TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        
        # Test suites table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_suites (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                last_run TEXT,
                status TEXT,
                failures INTEGER,
                fix_notes TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _insert_sample_data(self):
        """Insert sample data if tables are empty."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Check if we already have data
        cursor.execute("SELECT COUNT(*) FROM handovers")
        if cursor.fetchone()[0] == 0:
            current_time = datetime.now().isoformat()
            
            # Insert sample handovers
            sample_handovers = [
                ('1', 'Coverage', 'Analysis', '2024-01-15', 'Handover of regression test results', 
                 'test_report_001.pdf,coverage_metrics.xlsx', 'Completed', current_time, current_time),
                ('2', 'Analysis', 'Coverage', '2024-01-16', 'Return for additional test cases', 
                 'analysis_findings.pdf', 'Pending', current_time, current_time)
            ]
            cursor.executemany('INSERT INTO handovers VALUES (?,?,?,?,?,?,?,?,?)', sample_handovers)
            
            # Insert sample requirements
            sample_requirements = [
                ('1', 'Login functionality update', 'Add biometric authentication support', 
                 '2024-01-10', 'High', 'In Progress', current_time, current_time),
                ('2', 'Payment gateway integration', 'Support for new payment provider', 
                 '2024-01-12', 'Medium', 'Pending Review', current_time, current_time)
            ]
            cursor.executemany('INSERT INTO requirements VALUES (?,?,?,?,?,?,?,?)', sample_requirements)
            
            # Insert sample issues
            sample_issues = [
                ('1', 'Database connection timeout', 'Test environment DB times out after 30s', 
                 'Infrastructure', 'High', 'Open', 'Infrastructure Team', current_time, current_time),
                ('2', 'Slow test execution', 'Test suite taking 2x longer than usual', 
                 'Performance', 'Medium', 'In Progress', 'Performance Team', current_time, current_time)
            ]
            cursor.executemany('INSERT INTO issues VALUES (?,?,?,?,?,?,?,?,?)', sample_issues)
            
            # Insert sample test suites
            sample_test_suites = [
                ('1', 'Regression Suite', '2024-01-14', 'Failed', 3, 
                 'Addressing API timeout issues', current_time, current_time),
                ('2', 'Smoke Test Suite', '2024-01-15', 'Passed', 0, '', current_time, current_time)
            ]
            cursor.executemany('INSERT INTO test_suites VALUES (?,?,?,?,?,?,?,?)', sample_test_suites)
            
            conn.commit()
        
        conn.close()
    
    # Handover operations
    def add_handover(self, handover: Handover) -> str:
        """Add a new handover."""
        if not handover.validate():
            raise ValueError("Invalid handover data")
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO handovers (id, from_team, to_team, date, description, documents, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            handover.id,
            handover.from_team,
            handover.to_team,
            handover.date,
            handover.description,
            ','.join(handover.documents),
            handover.status,
            handover.created_at,
            handover.updated_at
        ))
        
        conn.commit()
        conn.close()
        return handover.id
    
    def update_handover(self, handover_id: str, handover: Handover):
        """Update an existing handover."""
        if not handover.validate():
            raise ValueError("Invalid handover data")
        
        handover.update_timestamp()
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE handovers 
            SET from_team = ?, to_team = ?, date = ?, description = ?, documents = ?, status = ?, updated_at = ?
            WHERE id = ?
        ''', (
            handover.from_team,
            handover.to_team,
            handover.date,
            handover.description,
            ','.join(handover.documents),
            handover.status,
            handover.updated_at,
            handover_id
        ))
        
        conn.commit()
        conn.close()
    
    def get_handovers(self, status_filter: Optional[str] = None) -> List[Handover]:
        """Get handovers with optional status filter."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = 'SELECT * FROM handovers'
        params = []
        
        if status_filter and status_filter != "All":
            query += ' WHERE status = ?'
            params.append(status_filter)
            
        query += ' ORDER BY updated_at DESC'
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        handovers = []
        for row in rows:
            handover_data = {
                'id': row[0],
                'from_team': row[1],
                'to_team': row[2],
                'date': row[3],
                'description': row[4],
                'documents': row[5].split(',') if row[5] else [],
                'status': row[6],
                'created_at': row[7],
                'updated_at': row[8]
            }
            handovers.append(Handover.from_dict(handover_data))
        
        return handovers
    
    def delete_handover(self, handover_id: str) -> bool:
        """Delete a handover by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM handovers WHERE id = ?', (handover_id,))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        return deleted
    
    # Requirement operations
    def add_requirement(self, requirement: Requirement) -> str:
        """Add a new requirement."""
        if not requirement.validate():
            raise ValueError("Invalid requirement data")
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO requirements (id, title, description, change_date, priority, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            requirement.id,
            requirement.title,
            requirement.description,
            requirement.change_date,
            requirement.priority,
            requirement.status,
            requirement.created_at,
            requirement.updated_at
        ))
        
        conn.commit()
        conn.close()
        return requirement.id
    
    def update_requirement(self, requirement_id: str, requirement: Requirement):
        """Update an existing requirement."""
        if not requirement.validate():
            raise ValueError("Invalid requirement data")
        
        requirement.update_timestamp()
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE requirements 
            SET title = ?, description = ?, change_date = ?, priority = ?, status = ?, updated_at = ?
            WHERE id = ?
        ''', (
            requirement.title,
            requirement.description,
            requirement.change_date,
            requirement.priority,
            requirement.status,
            requirement.updated_at,
            requirement_id
        ))
        
        conn.commit()
        conn.close()
    
    def get_requirements(self, status_filter: Optional[str] = None, 
                        priority_filter: Optional[str] = None) -> List[Requirement]:
        """Get requirements with optional filters."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = 'SELECT * FROM requirements'
        params = []
        conditions = []
        
        if status_filter and status_filter != "All":
            conditions.append('status = ?')
            params.append(status_filter)
            
        if priority_filter and priority_filter != "All":
            conditions.append('priority = ?')
            params.append(priority_filter)
            
        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)
            
        query += ' ORDER BY updated_at DESC'
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        requirements = []
        for row in rows:
            requirement_data = {
                'id': row[0],
                'title': row[1],
                'description': row[2],
                'change_date': row[3],
                'priority': row[4],
                'status': row[5],
                'created_at': row[6],
                'updated_at': row[7]
            }
            requirements.append(Requirement.from_dict(requirement_data))
        
        return requirements
    
    def delete_requirement(self, requirement_id: str) -> bool:
        """Delete a requirement by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM requirements WHERE id = ?', (requirement_id,))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        return deleted
    
    # Issue operations
    def add_issue(self, issue: Issue) -> str:
        """Add a new issue."""
        if not issue.validate():
            raise ValueError("Invalid issue data")
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO issues (id, title, description, type, priority, status, assigned_to, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            issue.id,
            issue.title,
            issue.description,
            issue.type,
            issue.priority,
            issue.status,
            issue.assigned_to,
            issue.created_at,
            issue.updated_at
        ))
        
        conn.commit()
        conn.close()
        return issue.id
    
    def update_issue(self, issue_id: str, issue: Issue):
        """Update an existing issue."""
        if not issue.validate():
            raise ValueError("Invalid issue data")
        
        issue.update_timestamp()
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE issues 
            SET title = ?, description = ?, type = ?, priority = ?, status = ?, assigned_to = ?, updated_at = ?
            WHERE id = ?
        ''', (
            issue.title,
            issue.description,
            issue.type,
            issue.priority,
            issue.status,
            issue.assigned_to,
            issue.updated_at,
            issue_id
        ))
        
        conn.commit()
        conn.close()
    
    def get_issues(self, type_filter: Optional[str] = None, 
                   status_filter: Optional[str] = None, 
                   priority_filter: Optional[str] = None) -> List[Issue]:
        """Get issues with optional filters."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = 'SELECT * FROM issues'
        params = []
        conditions = []
        
        if type_filter and type_filter != "All":
            conditions.append('type = ?')
            params.append(type_filter)
            
        if status_filter and status_filter != "All":
            conditions.append('status = ?')
            params.append(status_filter)
            
        if priority_filter and priority_filter != "All":
            conditions.append('priority = ?')
            params.append(priority_filter)
            
        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)
            
        query += ' ORDER BY updated_at DESC'
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        issues = []
        for row in rows:
            issue_data = {
                'id': row[0],
                'title': row[1],
                'description': row[2],
                'type': row[3],
                'priority': row[4],
                'status': row[5],
                'assigned_to': row[6],
                'created_at': row[7],
                'updated_at': row[8]
            }
            issues.append(Issue.from_dict(issue_data))
        
        return issues
    
    def delete_issue(self, issue_id: str) -> bool:
        """Delete an issue by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM issues WHERE id = ?', (issue_id,))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        return deleted
    
    # Test Suite operations
    def add_test_suite(self, test_suite: TestSuite) -> str:
        """Add a new test suite."""
        if not test_suite.validate():
            raise ValueError("Invalid test suite data")
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO test_suites (id, name, last_run, status, failures, fix_notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            test_suite.id,
            test_suite.name,
            test_suite.last_run,
            test_suite.status,
            test_suite.failures,
            test_suite.fix_notes,
            test_suite.created_at,
            test_suite.updated_at
        ))
        
        conn.commit()
        conn.close()
        return test_suite.id
    
    def update_test_suite(self, test_suite_id: str, test_suite: TestSuite):
        """Update an existing test suite."""
        if not test_suite.validate():
            raise ValueError("Invalid test suite data")
        
        test_suite.update_timestamp()
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE test_suites 
            SET name = ?, last_run = ?, status = ?, failures = ?, fix_notes = ?, updated_at = ?
            WHERE id = ?
        ''', (
            test_suite.name,
            test_suite.last_run,
            test_suite.status,
            test_suite.failures,
            test_suite.fix_notes,
            test_suite.updated_at,
            test_suite_id
        ))
        
        conn.commit()
        conn.close()
    
    def get_test_suites(self, status_filter: Optional[str] = None) -> List[TestSuite]:
        """Get test suites with optional status filter."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = 'SELECT * FROM test_suites'
        params = []
        
        if status_filter and status_filter != "All":
            query += ' WHERE status = ?'
            params.append(status_filter)
            
        query += ' ORDER BY updated_at DESC'
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        test_suites = []
        for row in rows:
            test_suite_data = {
                'id': row[0],
                'name': row[1],
                'last_run': row[2],
                'status': row[3],
                'failures': row[4],
                'fix_notes': row[5],
                'created_at': row[6],
                'updated_at': row[7]
            }
            test_suites.append(TestSuite.from_dict(test_suite_data))
        
        return test_suites
    
    def delete_test_suite(self, test_suite_id: str) -> bool:
        """Delete a test suite by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM test_suites WHERE id = ?', (test_suite_id,))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        return deleted
    
    def get_recent_activities(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent activities from all tables combined."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Get recent handovers
        cursor.execute('''
            SELECT 'handover' as type, id, from_team || ' → ' || to_team as title, description, 
                   date as timestamp, status, updated_at
            FROM handovers 
            ORDER BY updated_at DESC 
            LIMIT ?
        ''', (limit,))
        handovers = cursor.fetchall()
        
        # Get recent requirements
        cursor.execute('''
            SELECT 'requirement' as type, id, title, description, 
                   change_date as timestamp, status, updated_at
            FROM requirements 
            ORDER BY updated_at DESC 
            LIMIT ?
        ''', (limit,))
        requirements = cursor.fetchall()
        
        # Get recent issues
        cursor.execute('''
            SELECT 'issue' as type, id, title, description, 
                   created_at as timestamp, status, updated_at
            FROM issues 
            ORDER BY updated_at DESC 
            LIMIT ?
        ''', (limit,))
        issues = cursor.fetchall()
        
        # Get recent test suites
        cursor.execute('''
            SELECT 'test_suite' as type, id, name as title, fix_notes as description, 
                   last_run as timestamp, status, updated_at
            FROM test_suites 
            ORDER BY updated_at DESC 
            LIMIT ?
        ''', (limit,))
        test_suites = cursor.fetchall()
        
        conn.close()
        
        # Combine all activities
        all_activities = []
        for activity in handovers + requirements + issues + test_suites:
            all_activities.append({
                'type': activity[0],
                'id': activity[1],
                'title': activity[2],
                'description': activity[3],
                'timestamp': activity[4],
                'status': activity[5],
                'updated_at': activity[6]
            })
        
        # Sort by updated_at timestamp (most recent first)
        all_activities.sort(key=lambda x: x['updated_at'], reverse=True)
        return all_activities[:limit]
