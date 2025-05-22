from flask import current_app, session
import uuid
import re
import datetime
import json

class VirtualReport:
    def __init__(self):
        pass

    def get_reports(self, limit, offset, search_value, order_column, order_dir, column_search):
        """Get reports with pagination, sorting and filtering"""
        # Build where conditions and params
        where_conditions = []
        params = {}
        
        # Process column-specific search
        if column_search:
            for idx, search_text in column_search.items():
                idx = int(idx) if str(idx).isdigit() else idx
                if isinstance(idx, int) and 0 <= idx < 4 and search_text and search_text.strip():
                    param_name = f"col_search_{idx}"
                    if idx == 0:  # ID column
                        where_conditions.append("r.id LIKE :"+param_name)
                    elif idx == 1:  # Title column
                        where_conditions.append("p1.title LIKE :"+param_name)
                    elif idx == 2:  # Controller column
                        where_conditions.append("p2.controller LIKE :"+param_name)
                    elif idx == 3:  # Name column
                        where_conditions.append("r.name LIKE :"+param_name)
                    
                    params[param_name] = f"%{search_text.strip()}%"
        
        # Add global search if provided
        if search_value:
            global_search = []
            global_search.append("r.id LIKE :search_id")
            params["search_id"] = f"%{search_value}%"
            global_search.append("p1.title LIKE :search_title")
            params["search_title"] = f"%{search_value}%"
            global_search.append("p2.controller LIKE :search_controller")
            params["search_controller"] = f"%{search_value}%"
            global_search.append("r.name LIKE :search_name")
            params["search_name"] = f"%{search_value}%"
            
            where_conditions.append("(" + " OR ".join(global_search) + ")")
        
        # Base Query with Filtering
        where_sql = " WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        query = f"""
            WITH ReportData AS (
                SELECT r.id, r.name, p1.title, p2.controller, r.created_by, r.date_created, r.last_run, r.[is_public],
                    ROW_NUMBER() OVER (ORDER BY {order_column} {order_dir}) AS RowNum
                FROM [VirtualReports].[dbo].[reports] r
                LEFT JOIN [JADVDATA].[dbo].[permissions] p1 ON p1.id = r.link_id 
                LEFT JOIN [JADVDATA].[dbo].[permissions] p2 ON p2.id = p1.parent_id
                {where_sql}
            ) 
            SELECT * FROM ReportData WHERE RowNum BETWEEN :row_start AND :row_end
        """
        
        # Add pagination parameters
        params["row_start"] = offset + 1  # MSSQL RowNum starts at 1
        params["row_end"] = offset + limit
        
        # Execute Query
        rows = current_app.db.fetch_all(query, params)
        
        # Get total count (without filtering)
        count_query = "SELECT COUNT(*) AS total FROM [VirtualReports].[dbo].[reports]"
        total_records_result = current_app.db.fetch(count_query)
        total_records = total_records_result['total'] if total_records_result else 0
        
        # Get filtered count
        total_filtered_records = total_records
        if where_conditions:
            count_filtered_query = f"""
                SELECT COUNT(*) AS total FROM [VirtualReports].[dbo].[reports] r
                LEFT JOIN [JADVDATA].[dbo].[permissions] p1 ON p1.id = r.link_id 
                LEFT JOIN [JADVDATA].[dbo].[permissions] p2 ON p2.id = p1.parent_id
                {where_sql}
            """
            filtered_params = {k: v for k, v in params.items() if k not in ["row_start", "row_end"]}
            filtered_records_result = current_app.db.fetch(count_filtered_query, filtered_params)
            total_filtered_records = filtered_records_result['total'] if filtered_records_result else 0
        
        return {
            "data": rows,
            "recordsTotal": total_records,
            "recordsFiltered": total_filtered_records
        }
        
    def get_report_by_id(self, report_id):
        """Get a report by ID"""
        query = "SELECT * FROM [VirtualReports].[dbo].[reports] WHERE [id]=:report_id"
        report = current_app.db.fetch(query, {"report_id": report_id})
        
        if report:
            
            if report.get('variables'):
                report.parse_json('variables')
                
            if report.get('columns'):
                report.parse_json('columns')
            
            
            # Get link info
            if report.get('link_id'):
                link_query = "SELECT * FROM [JADVDATA].[dbo].[permissions] WHERE id=:link_id"
                link = current_app.db.fetch(link_query, {"link_id": report['link_id']})
                if link:
                    report['link_parent'] = link['parent_id']
                    report['link_text'] = link['title']
            
            # Update the last_run timestamp
            update_query = """
                UPDATE [VirtualReports].[dbo].[reports]
                SET [last_run] = GETDATE()
                WHERE [id] = :report_id
            """
            current_app.db.execute(update_query, {"report_id": report_id})
            
            return report
        
        return None
    
    def create_permission_for_report(self, report_id):
        """Create a permission for a report and return the link ID"""
        query = """
            INSERT INTO [JADVDATA].[dbo].[permissions]
            ([folder],[controller],[page],[namespace],[title],[parent_id],[menu_link],[development],
             [linked_to],[grouper],[validate],[order_number],[updated_by])
            VALUES ('','techops',:page,'','---NAME---','517','1','0','0','0','1','0','0'); 
            SELECT SCOPE_IDENTITY() AS id
        """
        result = current_app.db.fetch(query, {"page": f'viewReport/{report_id}'})
        if result:
            link_id = result['id']
            update_query = "UPDATE [VirtualReports].[dbo].[reports] SET [link_id]=:link_id WHERE [id]=:report_id"
            current_app.db.execute(update_query, {"link_id": link_id, "report_id": report_id})
            return link_id
        return None
    
    def get_groupers(self):
        """Get groupers for permissions"""
        query = """
            SELECT * FROM [JADVDATA].[dbo].[permissions] 
            WHERE GROUPER='1' 
            ORDER BY controller ASC, menu_link DESC, development ASC
        """
        return current_app.db.fetch_all(query)
    
    def get_all_reports(self):
        """Get all reports for dropdown"""
        query = "SELECT * FROM [VirtualReports].[dbo].[reports] ORDER BY name ASC"
        return current_app.db.fetch_all(query)
    
    def format_column_display(self, column):
        """Format column name for display"""
        # Split on underscores and insert space before capitals
        with_spaces = re.sub(r'(?<=[a-z])(?=[A-Z])|_', ' ', column)
        
        # Split into words
        words = with_spaces.strip().split(' ')
        
        # Process each word
        result = []
        for word in words:
            if len(word) <= 3 and word:
                # Uppercase words less than 4 characters
                result.append(word.upper())
            else:
                # Just capitalize first letter for longer words
                result.append(word.capitalize())
        
        # Join with spaces for display
        return ' '.join(result)

    def create_temp_table_for_list(self, var_name, values):
        """Create a temporary table for list variables"""
        temp_table = f"#temp_{uuid.uuid4().hex}"
        create_query = "CREATE TABLE :table_name (value VARCHAR(255));"
        current_app.db.execute(create_query, {"table_name": temp_table})
        
        for value in values:
            insert_query = "INSERT INTO :table_name (value) VALUES (:value)"
            current_app.db.execute(insert_query, {"table_name": temp_table, "value": value})
        
        return temp_table

    def drop_temp_table(self, table_name):
        """Drop a temporary table"""
        query = "DROP TABLE IF EXISTS :table_name"
        current_app.db.execute(query, {"table_name": table_name})
        
    def execute_report_query(self, query):
        """Execute a report query and return the results"""
        return current_app.db.fetch(query)
        
    def get_report_stats(self):
        """Get statistics for reports"""
        query = """
            SELECT 
                COUNT(*) as total_reports,
                SUM(CASE WHEN last_run > DATEADD(day, -7, GETDATE()) THEN 1 ELSE 0 END) as recent_runs,
                SUM(CASE WHEN [is_public] = 0 THEN 1 ELSE 0 END) as public_reports,
                MAX(date_created) as newest_report
            FROM [VirtualReports].[dbo].[reports]
        """
        return current_app.db.fetch(query)

    def get_columns_from_test_query(self, query,params):
        """Get columns from a test query execution"""
        
        # Fetch columns from last query result
        row = current_app.db.fetch(query,params)
        columns = []
        if row:
            for column in row.keys():
                columns.append({
                    'name': column,
                    'display': self.format_column_display(column),
                    'type': 'text',
                    'desc': ''
                })
        
        return columns

    def has_permission(self, user_id, report_id):
        """Check if a user has permission to view a report"""
        if not user_id:
            return False
        
        # Example permission check - customize as needed
        query = """
            SELECT 1 FROM [JADVDATA].[dbo].[permissions_rights] ur
            JOIN [JADVDATA].[dbo].[permissions] p ON p.id = ur.permission_id
            JOIN [VirtualReports].[dbo].[reports] r ON r.link_id = p.id
            WHERE r.user_id = :user_id AND r.id = :report_id
        """
        
        try:
            result = current_app.db.fetch(query, {"user_id": user_id, "report_id": report_id})
            return result is not None
        except:
            # Fall back to admin check if query fails
            return user_id in [111, 123]

    def log_report_run(self, report_id, user_id=None):
        """Log a report run for statistics"""
        try:
            # Try to log to ReportRuns table if it exists
            query = """
                INSERT INTO [VirtualReports].[dbo].[report_runs]
                ([report_id], [user_id], [run_date])
                VALUES (:report_id, :user_id, GETDATE())
            """

            current_app.db.execute(query, {"report_id": report_id, "user_id": user_id or 0})
        except:
            # Table might not exist yet, just update last_run
            pass

    def get_recent_reports(self, limit=10):
        """Get most recently used reports"""
        query = """
            SELECT TOP :limit id, name, last_run, created_by
            FROM [VirtualReports].[dbo].[reports]
            WHERE last_run IS NOT NULL
            ORDER BY last_run DESC
        """
        return current_app.db.fetch_all(query, {"limit": limit})

    def get_popular_reports(self, limit=10):
        """Get most popular reports"""
        try:
            # Try to get from ReportRuns if the table exists
            query = """
                SELECT TOP :limit r.id, r.name, COUNT(*) as run_count
                FROM [VirtualReports].[dbo].[report_runs] rr
                JOIN [VirtualReports].[dbo].[reports] r ON r.id = rr.report_id
                GROUP BY r.id, r.name
                ORDER BY run_count DESC
            """
            return current_app.db.fetch_all(query, {"limit": limit})
        except:
            # Fall back to last_run if the ReportRuns table doesn't exist
            query = """
                SELECT TOP :limit id, name, 0 as run_count
                FROM [VirtualReports].[dbo].[reports]
                WHERE last_run IS NOT NULL
                ORDER BY last_run DESC
            """
            return current_app.db.fetch_all(query, {"limit": limit})

    def create_new_report(self, params: dict) -> int:
        """
        Create a new report, filling out every column with either the provided value or a default.
        Returns the new report ID.
        """
        defaults = {
            'name': '_NEW Report',
            'display': '',
            'query': '',
            'description': '',
            'columns': '',
            'variables': '',
            'alternate_id': 0,
            'alternate_text': '',
            'link_id': 0,
            'related_report': -1,
            'limit_by_user': False,
            'limit_display': False,
            'is_wide': False,
            'is_ajax': False,
            'is_auto_run': False,
            'is_searchable': True,
            'is_public': False,
            'is_download_csv': False,
            'is_download_xlsx': False,
        }

        cfg = {**defaults, **params}

        missing = [k for k, v in cfg.items() if v is None]
        if missing:
            raise ValueError(f"Missing values for: {', '.join(missing)}")

        user_id = (
            current_app.get_current_user_id()
            if hasattr(current_app, 'get_current_user_id')
            else 0
        )
        cfg['created_by'] = user_id

        # convert Y/N or bool to 1/0
        bool_fields = (
            'limit_by_user', 'limit_display', 'is_wide', 'is_ajax',
            'is_auto_run', 'is_searchable', 'is_public',
            'is_download_csv', 'is_download_xlsx'
        )
        for field in bool_fields:
            val = cfg[field]
            if isinstance(val, str):
                upper = val.upper()
                if upper == 'Y':
                    val = True
                elif upper == 'N':
                    val = False
                else:
                    val = bool(int(val))
            cfg[field] = 1 if bool(val) else 0

        query = """
            INSERT INTO [VirtualReports].[dbo].[reports]
                ([name], [display], [query], [description], [columns], [variables],
                [alternate_id], [alternate_text], [link_id], [related_report],
                [limit_by_user], [limit_display], [is_wide], [is_ajax],
                [is_auto_run], [is_searchable], [is_public],
                [is_download_csv], [is_download_xlsx],
                [date_created], [created_by])
            VALUES
                (:name, :display, :query, :description, :columns, :variables,
                :alternate_id, :alternate_text, :link_id, :related_report,
                :limit_by_user, :limit_display, :is_wide, :is_ajax,
                :is_auto_run, :is_searchable, :is_public,
                :is_download_csv, :is_download_xlsx,
                GETDATE(), :created_by);
            SELECT SCOPE_IDENTITY() AS new_id;
        """

        result = current_app.db.fetch(query, cfg)
        report_id = result['new_id'] if result else None
        return {
            'success': report_id is not None,
            'report_id': report_id
        }

    def delete(self, report_id):
        """Delete a report by ID and return success status"""
        query = """
            DELETE FROM [VirtualReports].[dbo].[reports]
            WHERE [id] = :report_id
        """
        
        result = current_app.db.execute(query, {"report_id": report_id})
        
        # Check if any rows were affected
        if result and result > 0:
            return True
        return False        
    
    def update_report(self, data):
        """Update a report"""
        # Process Yes/No fields
        limit_by_user = 1 if data.get('limit_by_user') else 0
        limit_display = 1 if data.get('limit_display') else 0
        is_wide = 1 if data.get('is_wide') else 0
        is_ajax = 1 if data.get('is_ajax') else 0
        is_public = 1 if data.get('is_public') else 0
        is_auto_run = 1 if data.get('is_auto_run') else 0
        is_searchable = 1 if data.get('is_searchable') else 0
        
        # Process columns
        columns = []
        for column in data.get('columns', []):
            if column.get('name') and column['name'].strip():
                columns.append(column)
        
        # Process variables
        variables = []
        for variable in data.get('variables', []):
            if variable.get('name') and variable['name'].strip():
                variables.append(variable)
        
        # Prepare data for update
        report_id = data['id']
        name = data['name']
        display = data.get('display', name)
        description = data.get('description', '')
        query = data.get('query', '').strip()
        query = query.rstrip(';')
        
        # Serialize columns and variables
        serialized_columns = json.dumps(columns)
        serialized_variables = json.dumps(variables)
        
        # Handle related report
        related_report = data.get('related_report')
        if related_report == "--NONE--":
            related_report = -1
        
        # Update report
        update_query = """
            UPDATE [VirtualReports].[dbo].[reports]
             SET [is_wide]=:is_wide,
                [limit_display]=:limit_display,
                [limit_by_user]=:limit_by_user,
                [related_report]=:related_report,
                [description]=:description,
                [name]=:name,
                [display]=:display,
                [query]=:query,
                [columns]=:columns,
                [variables]=:variables,
                [is_ajax]=:is_ajax,
                [is_auto_run]=:is_auto_run,
                [is_searchable]=:is_searchable,
                [is_public]=:is_public
             WHERE [id]=:report_id
        """
        update_params = {
            "is_wide": is_wide,
            "limit_display": limit_display,
            "limit_by_user": limit_by_user,
            "related_report": related_report,
            "description": description,
            "name": name,
            "display": display,
            "query": query,
            "columns": serialized_columns,
            "variables": serialized_variables,
            "is_ajax": is_ajax,
            "is_auto_run": is_auto_run,
            "is_searchable": is_searchable,
            "is_public": is_public,
            "report_id": report_id
        }
        current_app.db.execute(update_query, update_params)
        
        # Update permission
        link_id = data.get('link_id')
        link_text = data.get('link_text')
        link_parent = data.get('link_parent')
        
        if link_id and link_text and link_parent:
            update_perm_query = """
                UPDATE [JADVDATA].[dbo].[permissions]
                 SET [title]=:title,
                    [parent_id]=:parent_id
                 WHERE [id]=:id
            """
            current_app.db.execute(update_perm_query, {"title": link_text, "parent_id": link_parent, "id": link_id})
    
    def get_report_for_view(self, report_id):
        """Get report data for viewing"""
        query = """
            SELECT [id],[name],[display],[query],[description],[columns],[alternate_id],[alternate_text], [variables],
                  [link_id],[related_report],[limit_by_user],[limit_display],[is_wide],[is_ajax],[is_auto_run],
                  [is_searchable],[is_public],[created_by],[date_created],[last_run]
            FROM [VirtualReports].[dbo].[reports]
             WHERE [id]=:report_id
        """
        report = current_app.db.fetch(query, {"report_id": report_id})
        
        if report:
            if report.get('variables'):
                report.parse_json('variables')
            
            if report.get('columns'):
                report.parse_json('columns')
            
            if report.get('related_report'):
                related_query = "SELECT * FROM [VirtualReports].[dbo].[reports] WHERE [id]=:related_id"
                report['related'] = current_app.db.fetch(related_query, {"related_id": report['related_report']})
            
            # Update the last_run timestamp
            update_query = """
                UPDATE [VirtualReports].[dbo].[reports]
                SET [last_run] = GETDATE()
                WHERE [id] = :report_id
            """
            current_app.db.execute(update_query, {"report_id": report_id})
            
            return report
        
        return None
    
    def run_report_query(self, request):
        """Process report data request from DataTables POST format"""
        import traceback
        
        # Get POST parameters from DataTables format
        post_data = request.form if request.form else request.get_json()
        
        # Extract report ID from request
        report_id = post_data.get('report_id')
        
        # Extract pagination parameters
        draw = int(post_data.get('draw', 1))
        start = int(post_data.get('start', 0))
        length = int(post_data.get('length', 10))
        
        # Extract search value (global search)
        search_value = post_data.get('search[value]', '')
        
        # Extract column ordering
        order_column_idx = post_data.get('order[0][column]')
        order_dir = post_data.get('order[0][dir]', 'asc')
        
        # Extract column information and individual column searches
        columns_data = {}
        column_search = {}
        
        # Parse column data from DataTables format
        for key in post_data:
            if key.startswith('columns[') and key.endswith('][data]'):
                # Extract column index from the key
                idx = key[8:key.find(']')]
                columns_data[idx] = post_data[key]
                
                # Get corresponding search value for this column
                search_key = f'columns[{idx}][search][value]'
                if search_key in post_data and post_data[search_key]:
                    column_search[idx] = post_data[search_key]
        
        # Extract vars parameters
        vars_form = {}
        for key in post_data:
            if key.startswith('vars['):
                var_name = key[5:-1]  # Extract variable name from vars[name]
                vars_form[var_name] = post_data[key]


        
        try:
            report = self.get_report_by_id(report_id)
            
            

            if not report:
                return {"error": "No DB ROW"}, 404
            

            master_columns = report.columns  
            headers = []
            for col in master_columns:
                headers.append(col.name)
            
            # Build ORDER BY clause based on DataTables order
            order_by = []
            if order_column_idx is not None:
                # Get the actual column name based on the index
                order_column_name = columns_data.get(order_column_idx)
                # Find the corresponding position in headers if needed
                # This depends on how your column names map
                order_by.append(f"[{order_column_name}] {order_dir.upper()}")
            
            # Add default ordering if none specified
            if not order_by and headers:
                order_by.append(f"[{headers[0]}] ASC")
            
            order_clause = f"ORDER BY {','.join(order_by)}" if order_by else ""
            
            # Build WHERE clause from column-specific searches
            filter_conditions = []
            
            # Add column-specific searches
            for idx, search_text in column_search.items():
                column_name = columns_data.get(idx)
                if column_name and search_text:
                    filter_conditions.append(f"[{column_name}] LIKE '%{search_text.upper().strip()}%'")
            
            # Add global search if provided
            if search_value:
                global_conditions = []
                for col_name in headers:
                    global_conditions.append(f"[{col_name}] LIKE '%{search_value.upper().strip()}%'")
                
                if global_conditions:
                    filter_conditions.append(f"({' OR '.join(global_conditions)})")
            
            where_clause = f"WHERE {' AND '.join(filter_conditions)}" if filter_conditions else ""
            
            # Get the base query
            base_query = report.query  # Assuming already decoded from base64 in your ORM
            base_query = base_query.strip().rstrip(';')
            
            # Process any query variables from vars_form
            for name, value in vars_form.items():
                base_query = base_query.replace(f"{{{name}}}", str(value))
            
            # Add user limitation if needed
            user_id = session.get('user_id')
            if hasattr(report, 'limit_by_user') and report.limit_by_user == "Y":
                base_query = base_query.replace("--*USER*", " ")
                base_query = base_query.replace("{user_id}", str(user_id))
            
            # Build column list
            cols = [f"[{c.name}]" for c in master_columns]
            
            # Build final query with pagination
            mega_query = f"""
            SELECT {','.join(cols)}
            FROM 
                (
                    SELECT ROW_NUMBER() OVER ( {order_clause} ) AS RowNo, * 
                    FROM
                    (   
                        SELECT * 
                        FROM 
                        ({base_query}
                        ) as INTERNAL
                    ) as WRAPPEDROWS
                    {where_clause}
                ) as PAGINATED
                WHERE RowNo > {start} AND RowNo <= {start + length}
            """
            # Execute the main query
            #print(mega_query)
            #print(vars_form)
            results = current_app.db.fetch_all(mega_query,vars_form)
            
            # Get total count
            count_query = f"SELECT COUNT(*) as count FROM ({base_query}) as int1"
            count_result = current_app.db.fetch(count_query,vars_form)
            total_rows = count_result.count if count_result else 0
            
            # Get filtered count
            filtered_count_query = f"SELECT COUNT(*) as count FROM ({base_query}) as int1 {where_clause}"
            filtered_count_result = current_app.db.fetch(filtered_count_query,vars_form)
            filtered_rows = filtered_count_result.count if filtered_count_result else 0
            
            # Prepare response data in DataTables format
            data = {
                "draw": draw,
                "recordsTotal": total_rows,
                "recordsFiltered": filtered_rows,
                "data": results,
                "headers": headers
            }
            
            return data
            
        except Exception as e:
            #print(f"Error processing report data: {e}")
            #print(traceback.format_exc())
            return {
                "draw": draw,
                "recordsTotal": 0,
                "recordsFiltered": 0,
                "data": [],
                "error": str(e)
            }