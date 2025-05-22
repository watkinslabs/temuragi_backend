import random
import re
import secrets
import time
from datetime import datetime, date
from typing import Optional, List, Dict, Any, Tuple
import requests
from flask import g, current_app


class CustomerManager:
    """
    Handles customer creation and management in the database tables:
    - bkarcust
    - bkphone 
    - bkarpr
    - bkarcprc
    """
    def __init__(self, region="GPACIFIC"):
        """
        Initialize customer manager
        
        Args:
            region: Region code (GPACIFIC or GCANADA)
        """
        self.region = region  # GPACIFIC or GCANADA
        self.errors = []
        self.customer_code = -1
    
    @property
    def db(self):
        # Get db from current_app if not provided in init
        if hasattr(g, 'db'):
            return g.db
        return current_app.db
    
    @property
    def logger(self):
        # Get logger from app or current_app
        return current_app.logger

    
    def random_password(self, len_param: int = 6) -> str:
        """
        Generates a random password with consonant+vowel pairs followed by two digits
        
        Args:
            len_param: The desired length of the password (must be even)
            
        Returns:
            A random password string
        """
        if len_param % 2 != 0:
            len_param = 8  # Default to 8 if not even
        
        # Account for the two-digit number on the end
        length = len_param - 2
        pair_length = length // 2
        
        consonants = 'bcdfghjklmnprstvwxyz'
        vowels = 'aeiou'
        
        password = ''
        for _ in range(pair_length):
            password += random.choice(consonants)
            password += random.choice(vowels)
            
        password += str(random.randint(10, 99))
        return password
    
    def sanitize_phone(self, phone: str) -> str:
        """
        Removes non-digit characters from phone numbers
        
        Args:
            phone: The phone number string to sanitize
            
        Returns:
            Sanitized phone number with only digits
        """
        if not phone:
            return ""
        return re.sub(r'\D+', '', phone)
    
    def get_zip_data(self, zip_code: str) -> Optional[Dict]:
        """
        Look up city, state and sales person info from zip code
        
        Args:
            zip_code: The zip/postal code
            
        Returns:
            Dictionary with city, state, and sales person info or None if not found
        """
        if not zip_code:
            return None
            
        try:
            # Handle different zip code formats (US vs Canadian)
            if zip_code[0].isdigit():
                # US zip code
                query = "SELECT * FROM JADVDATA.dbo.BKZIP WHERE BKZIP.BKZIP_ZIP=:zip_code"
                params = {"zip_code": zip_code[:5]}
            else:
                # Canadian postal code
                query = "SELECT * FROM JADVDATA.dbo.BKZIP WHERE BKZIP.BKZIP_ZIP=:zip_code"
                params = {"zip_code": zip_code[:7]}
            
            result = self.db.fetch(query, params)
            if not result:
                return None
            zip_code = result['BKZIP_ZIP']

            if len(zip_code) == 7 and ' ' in zip_code:
                country  = 'CANADA'
            elif zip_code.isdigit():
                country  = 'US'
            else:
                country = None
            

            return {
                'city': result['BKZIP_CITY'],
                'state': result['BKZIP_STATE'],
                'country': country,
                'sales_person': result['BKZIP_SLSP']
            }
            
        except Exception as e:
            error_msg = f"Error getting zip data: {str(e)}"
            self.errors.append(error_msg)
            self.logger.error(error_msg)
            return None
    
    def check_phone_exists(self, phone: str) -> Optional[str]:
        """
        Check if phone number already exists in the system
        
        Args:
            phone: Phone number to check
            
        Returns:
            Customer code if exists, None otherwise
        """
        if not phone:
            return None
            
        try:
            query = f"SELECT TOP 1 * FROM {self.region}.dbo.BKPHONE WHERE BKPHONE_PHONE=:phone"
            result = self.db.fetch(query, {"phone": phone})
            
            if result:
                return result['BKPHONE_CSTCOD']
            
            return None
            
        except Exception as e:
            error_msg = f"Error checking phone existence: {str(e)}"
            self.errors.append(error_msg)
            self.logger.error(error_msg)
            return None
    
    def get_next_customer_code(self) -> int:
        """
        Get next available customer code from the master table
        
        Returns:
            Next customer code or -1 if error
        """
        try:
            # Get current code
            query = f"SELECT [BKSY_MSTR_CNUM] as code FROM [{self.region}].[dbo].[BKSYMSTR]"
            result = self.db.fetch(query)
            
            if not result:
                self.errors.append("Could not get next customer code")
                return -1
                
            code = result['code']
            
            # Increment the counter
            update_query = f"UPDATE [{self.region}].[dbo].[BKSYMSTR] SET [BKSY_MSTR_CNUM]=[BKSY_MSTR_CNUM]+1"
            self.db.execute(update_query)
            
            return code
            
        except Exception as e:
            error_msg = f"Error getting next customer code: {str(e)}"
            self.errors.append(error_msg)
            self.logger.error(error_msg)
            return -1
    
    def create_customer(self, customer_data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """
        Create a new customer with all related records
        
        Args:
            customer_data: Dictionary containing customer information
            user_id: ID of the user creating the customer
            
        Returns:
            Dictionary with status, customer code, and any errors
        """

        self.logger.info(f"Creating customer. User ID: {user_id}, Region: {self.region}")

        # Start with a clean error list
        self.errors = []
        
        # Extract and validate data
        customer_name = customer_data.get('customer_name', '')
        address1 = customer_data.get('address1', '')
        address2 = customer_data.get('address2', '')
        zip_code = customer_data.get('zip_code', '')
        customer_class = customer_data.get('customer_class', '')
        phone_number = self.sanitize_phone(customer_data.get('phone_number', ''))
        phone_ext = customer_data.get('phone_ext', '')
        phone_desc = customer_data.get('phone_desc', '')
        fax_number = self.sanitize_phone(customer_data.get('fax_number', ''))
        contact_person = customer_data.get('contact_person', '')
        email = customer_data.get('email', '')
        comments1 = customer_data.get('comments1', '')
        comments2 = customer_data.get('comments2', '')
        
        # Optional fields with defaults
        mail_preference = customer_data.get('mail_preference', 'N')
        po_required = customer_data.get('po_required', 'N')
        saturday_delivery = customer_data.get('saturday_delivery', 'N')
        lucky7 = customer_data.get('lucky7', 'N')
        statement_type = customer_data.get('statement_type', '')
        
        # Validate required fields
        if not customer_name:
            self.errors.append("Customer name is required")
        
        if not address1:
            self.errors.append("Address is required")
        
        if not zip_code:
            self.errors.append("Zip/Postal code is required")
        
        if not phone_number:
            self.errors.append("Phone number is required")
        
        # Get city, state from zip code
        zip_data = self.get_zip_data(zip_code)
        if not zip_data:
            self.errors.append("Invalid Zip/Postal Code")
            city = ""
            state = ""
            sales_person = ""
        else:
            city = zip_data['city']
            state = zip_data['state']
            sales_person = zip_data['sales_person']
        
        # Check for duplicate phone
        existing_customer = self.check_phone_exists(phone_number)
        if existing_customer:
            self.errors.append(f"Duplicate Phone Record. Account: {existing_customer}")
        
        # Check for duplicate fax if provided
        if fax_number:
            existing_fax = self.check_phone_exists(fax_number)
            if existing_fax:
                self.errors.append(f"Duplicate Fax Record. Account: {existing_fax}")
        
        # Generate random password
        password = self.random_password()
        
        # If there are errors, return without creating
        if self.errors:
            return {
                'success': False,
                'customer_code': -1,
                'errors': self.errors
            }
        
        # Get next customer code
        customer_code = self.get_next_customer_code()
        if customer_code == -1:
            return {
                'success': False,
                'customer_code': -1,
                'errors': self.errors
            }
        
        self.customer_code = customer_code
        
        try:
            # 1. Insert bkarcust record
            cust_query = f"""
            INSERT INTO {self.region}.dbo.BKARCUST (
                BKAR_CUSTCODE, BKAR_CUSTNAME, BKAR_ADD1, BKAR_ADD2,
                BKAR_CITY, BKAR_STATE, BKAR_ZIP, BKAR_COUNTRY, BKAR_TELEPHONE,
                BKAR_FAX_PHONE, BKAR_CONTACT, BKAR_COMMENTS1, BKAR_COMMENTS2,
                BKAR_CLASS, BKAR_SLSP_NUM, BKAR_NEW_CUST, BKAR_STATEMENT,
                BKAR_CREDITLMT, BKAR_CHG_INTRST, BKAR_REMAINCRD, BKAR_OUTINV,
                BKAR_LASTSALE, BKAR_LASTPMT, BKAR_GROSS_MTD, BKAR_COGS_MTD,
                BKAR_NET_MTD, BKAR_PNET_MTD, BKAR_GROSS_YTD, BKAR_COGS_YTD,
                BKAR_NET_YTD, BKAR_PNET_YTD, BKAR_GROSS_LYR, BKAR_COGS_LYR,
                BKAR_NET_LYR, BKAR_PNET_LYR, BKAR_GROSS_PVAR, BKAR_COGS_PVAR,
                BKAR_NET_PVAR, BKAR_PNET_PVAR, BKAR_OUT_CREDIT, BKAR_TAX_AUTH,
                BKAR_TAX_YN, BKAR_TERMS_NUM, BKAR_START_DATE, BKAR_PRICE_MAT,
                BKAR_HIST_YN, BKAR_ACTIVE
            ) VALUES (
                :customer_code, :customer_name, :address1, :address2,
                :city, :state, :zip_code, :country, :phone_number,
                :fax_number, :contact_person, :comments1, :comments2,
                :customer_class, :sales_person, :new_cust, :statement_type,
                :credit_limit, :charge_interest, :remain_credit, :out_inv,
                :last_sale, :last_payment, :gross_mtd, :cogs_mtd,
                :net_mtd, :pnet_mtd, :gross_ytd, :cogs_ytd,
                :net_ytd, :pnet_ytd, :gross_lyr, :cogs_lyr,
                :net_lyr, :pnet_lyr, :gross_pvar, :cogs_pvar,
                :net_pvar, :pnet_pvar, :out_credit, :tax_auth,
                :tax_yn, :terms_num, :start_date, :price_mat,
                :hist_yn, :active
            )
            """

            cust_params = {
                "customer_code": customer_code,
                "customer_name": customer_name,
                "address1": address1,
                "address2": address2,
                "city": city,
                "state": state,
                "zip_code": zip_code,
                "country":  customer_data.get('country', 'US UNITED STATES'),
                "phone_number": phone_number,
                "fax_number": fax_number,
                "contact_person": contact_person,
                "comments1": comments1,
                "comments2": comments2,
                "customer_class": customer_class,
                "sales_person": sales_person,
                "new_cust": customer_data.get('new_cust', 'Y'),
                "statement_type": statement_type,
                "credit_limit": customer_data.get('credit_limit', 0),
                "charge_interest": customer_data.get('charge_interest', 'N'),
                "remain_credit": customer_data.get('remain_credit', 0),
                "out_inv": customer_data.get('out_inv', 0),
                "last_sale": customer_data.get('last_sale', date.today().strftime("%Y-%m-%d")),
                "last_payment": customer_data.get('last_payment', date.today().strftime("%Y-%m-%d")),
                "gross_mtd": customer_data.get('gross_mtd', 0),
                "cogs_mtd": customer_data.get('cogs_mtd', 0),
                "net_mtd": customer_data.get('net_mtd', 0),
                "pnet_mtd": customer_data.get('pnet_mtd', 0),
                "gross_ytd": customer_data.get('gross_ytd', 0),
                "cogs_ytd": customer_data.get('cogs_ytd', 0),
                "net_ytd": customer_data.get('net_ytd', 0),
                "pnet_ytd": customer_data.get('pnet_ytd', 0),
                "gross_lyr": customer_data.get('gross_lyr', 0),
                "cogs_lyr": customer_data.get('cogs_lyr', 0),
                "net_lyr": customer_data.get('net_lyr', 0),
                "pnet_lyr": customer_data.get('pnet_lyr', 0),
                "gross_pvar": customer_data.get('gross_pvar', 0),
                "cogs_pvar": customer_data.get('cogs_pvar', 0),
                "net_pvar": customer_data.get('net_pvar', 0),
                "pnet_pvar": customer_data.get('pnet_pvar', 0),
                "out_credit": customer_data.get('out_credit', 0),
                "tax_auth": customer_data.get('tax_auth', ''),
                "tax_yn": customer_data.get('tax_yn', 'N'),
                "terms_num": customer_data.get('terms_num', 0),
                "start_date": customer_data.get('start_date', date.today().strftime("%Y-%m-%d")),
                "price_mat": customer_data.get('price_mat', 0),
                "hist_yn": customer_data.get('hist_yn', 'N'),
                "active": customer_data.get('active', 'Y')
            }
            
            self.db.execute(cust_query, cust_params)
            
            # 2. Insert bkphone record (main phone)
            phone_query = f"""
            INSERT INTO {self.region}.dbo.BKPHONE (
                BKPHONE_CSTCOD, BKPHONE_PHONE, BKPHONE_TYPE,
                BKPHONE_EXT, BKPHONE_DESC
            ) VALUES (
                :customer_code, :phone_number, :phone_type,
                :phone_ext, :phone_desc
            )
            """
            
            phone_params = {
                "customer_code": customer_code,
                "phone_number": phone_number,
                "phone_type": "W",
                "phone_ext": phone_ext,
                "phone_desc": phone_desc
            }
            
            self.db.execute(phone_query, phone_params)
            
            # 3. Insert bkphone record (fax) if provided
            if fax_number:
                fax_query = f"""
                INSERT INTO {self.region}.dbo.BKPHONE (
                    BKPHONE_CSTCOD, BKPHONE_PHONE, BKPHONE_TYPE,
                    BKPHONE_EXT, BKPHONE_DESC
                ) VALUES (
                    :customer_code, :fax_number, :phone_type,
                    :phone_ext, :phone_desc
                )
                """
                
                fax_params = {
                    "customer_code": customer_code,
                    "fax_number": fax_number,
                    "phone_type": "F",
                    "phone_ext": "",
                    "phone_desc": "Fax"
                }
                
                self.db.execute(fax_query, fax_params)
            
            # 4. Insert bkarpr record (preferences)
            arpr_query = f"""
            INSERT INTO {self.region}.dbo.BKARPR (
                BKAR_PR_CSTCOD, BKAR_PR_TPWORD, BKAR_PR_MAIL,
                BKAR_PR_POREQ, BKAR_PR_SATURDY, BKAR_PR_LUCKY7,
                BKAR_PR_EMAIL, BKAR_PR_1SALE, BKAR_PR_2SALE,
                BKAR_PR_LSALE, BKAR_PR_FAX, BKAR_PR_1CALL,
                BKAR_PR_LCALL, BKAR_PR_NOTES, BKAR_PR_TAXID,
                BKAR_PR_SALESVD, BKAR_PR_SALESVT, BKAR_PR_TXIDEXP,
                BKAR_PR_PARENT, BKAR_PR_POINTS
            ) VALUES (
                :customer_code, :password, :mail_preference,
                :po_required, :saturday_delivery, :lucky7,
                :email, :first_sale, :second_sale,
                :last_sale, :fax, :first_call,
                :last_call, :notes, :tax_id,
                :sales_vd, :sales_vt, :tax_id_exp,
                :parent, :points
            )
            """

            arpr_params = {
                "customer_code":    customer_code,
                "password":         password,
                "mail_preference":  customer_data.get('mail_preference', 'N'),
                "po_required":      customer_data.get('po_required', 'N'),
                "saturday_delivery":customer_data.get('saturday_delivery', 'N'),
                "lucky7":           customer_data.get('lucky7', 'N'),
                "email":            email,
                "first_sale":       customer_data.get('first_sale', date.today().strftime("%Y-%m-%d")),
                "second_sale":      customer_data.get('second_sale',date.today().strftime("%Y-%m-%d")),
                "last_sale":        customer_data.get('last_sale', date.today().strftime("%Y-%m-%d")),
                "fax":              customer_data.get('fax', 'N'),
                "first_call":       customer_data.get('first_call', date.today().strftime("%Y-%m-%d")),
                "last_call":        customer_data.get('last_call', date.today().strftime("%Y-%m-%d")),
                "notes":            customer_data.get('preference_notes', ''),
                "tax_id":           customer_data.get('tax_id', ''),
                "sales_vd":         customer_data.get('sales_vd', date.today().strftime("%Y-%m-%d")),
                "sales_vt":         customer_data.get('sales_vt', '0'),
                "tax_id_exp":       customer_data.get('tax_id_exp',date.today().strftime("%Y-%m-%d")),
                "parent":           customer_data.get('parent', ''),
                "points":           customer_data.get('points', 0)
            }
            
            self.db.execute(arpr_query, arpr_params)
            
            # 5. Insert price class records
            if customer_class:
                # Get all family and level combinations for this class
                class_query = """
                SELECT [BKAR_CPDF_FMLY] as family, [BKAR_CPDF_LEVEL] as level 
                FROM [JADVDATA].[dbo].[BKARCPDF] 
                WHERE [BKAR_CPDF_CLASS]=:customer_class
                """
                class_results = self.db.fetch_all(class_query, {"customer_class": customer_class})
                
                for row in class_results:
                    family = row['family']
                    level = row['level']
                    
                    cprc_query = f"""
                    INSERT INTO {self.region}.dbo.BKARCPRC (
                        BKAR_CPRC_CODE, BKAR_CPRC_FMLY, BKAR_CPRC_LEVEL
                    ) VALUES (
                        :customer_code, :family, :level
                    )
                    """
                    
                    cprc_params = {
                        "customer_code": customer_code,
                        "family": family,
                        "level": level
                    }
                    
                    self.db.execute(cprc_query, cprc_params)
            
            
            # Generate web account via external call
            #self.generate_web_account(customer_code)
            
            return {
                'success': True,
                'customer_code': customer_code,
                'password': password,
                'errors': []
            }
            
        except Exception as e:
            error_msg = f"Error creating customer: {str(e)}"
            self.errors.append(error_msg)
            self.logger.error(error_msg)
            
            return {
                'success': False,
                'customer_code': -1,
                'errors': self.errors
            }

    def generate_web_account(self, customer_code: int) -> bool:
        """
        Generate web account for customer via external API call
        
        Args:
            customer_code: Customer code to generate account for
            
        Returns:
            True if successful, False otherwise
        """
        dir_name = "webcanada" if self.region == "GCANADA" else "webpacific"
        url = f"https://www.performanceradiator.com/generateAccount_ahoy.php?custCode={customer_code}&dir={dir_name}"
        
        try:
            self.logger.info(f"Generating Web Customer: {customer_code} {dir_name}")
            
            response = requests.get(
                url, 
                verify=False,  # Not recommended in production
                timeout=30
            )
            
            if response.status_code == 200:
                return True
            else:
                self.logger.error(f"Error generating web account. Status code: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error generating web account: {str(e)}")
            return False

    def lookup_by_phone_number(self, phone_number):
        """
        Look up customer information by phone number.
        
        Args:
            phone_number (str): The phone number to search for
            
        Returns:
            dict: Dictionary with success, status, and data if available
        """
        # Check if phone_number parameter exists
        if not phone_number:
            return {
                'success': False,
                'status': 'invalid',
                'message': 'Phone number is required'
            }

        # Validate the phone number
        is_valid, cleaned_number = self.validate_phone_number(phone_number)
        
        if not is_valid:
            return {
                'success': False,
                'status': 'invalid',
                'message': 'Phone number format is invalid',
                'cleaned_number': None
            }
        
        # Phone number is valid, perform the lookup
        query = f"""
        SELECT 
            b.BKPHONE_CSTCOD as customer_code,
            c.BKAR_CUSTNAME as customer_name,
            b.BKPHONE_PHONE as phone_number,
            b.BKPHONE_TYPE as phone_type,
            b.BKPHONE_EXT as phone_ext,
            b.BKPHONE_DESC as phone_desc
        FROM {self.region}.dbo.BKPHONE b
        JOIN {self.region}.dbo.BKARCUST c ON b.BKPHONE_CSTCOD = c.BKAR_CUSTCODE
        WHERE b.BKPHONE_PHONE = :phone_number
        """
        
        params = {"phone_number": cleaned_number}
        results = self.db.fetch(query, params)
        
        if results and len(results) > 0:
            return {
                'success': True,
                'status': 'exists',
                'phone_data': results,  # Return the first match as an object
                'cleaned_number': cleaned_number
            }
        else:
            return {
                'success': True,  # This is a success - we found that the number doesn't exist
                'status': 'unused',
                'message': 'Phone number is available for use',
                'cleaned_number': cleaned_number
            }

    def validate_phone_number(self,phone):
        """
        Validates phone numbers allowing 10 digits with various delimiter formats.
        
        Valid formats include:
        - 1234567890
        - 123-456-7890
        - 123.456.7890
        - 123 456 7890
        - (123) 456-7890
        - And variations of these
        
        Args:
            phone (str): Phone number to validate
            
        Returns:
            bool: True if valid, False otherwise
            str: Normalized phone number with only digits if valid, None otherwise
        """
        if not phone:
            return False, None
            
        # Strip all non-alphanumeric characters
        phone_stripped = re.sub(r'[^0-9a-zA-Z]', '', phone)
        
        # Check if it contains any alpha characters
        if re.search(r'[a-zA-Z]', phone_stripped):
            return False, None
        
        # Check if we have exactly 10 digits
        if len(phone_stripped) != 10:
            return False, None
        
        # Return the normalized version (digits only)
        return True, phone_stripped

    def validate_phone_number(self,phone):
        """
        Validates phone numbers allowing 10 digits with various delimiter formats.
        
        Valid formats include:
        - 1234567890
        - 123-456-7890
        - 123.456.7890
        - 123 456 7890
        - (123) 456-7890
        - And variations of these
        
        Args:
            phone (str): Phone number to validate
            
        Returns:
            bool: True if valid, False otherwise
            str: Normalized phone number with only digits if valid, None otherwise
        """
        if not phone:
            return False, None
            
        # Strip all non-alphanumeric characters
        phone_stripped = re.sub(r'[^0-9a-zA-Z]', '', phone)
        
        # Check if it contains any alpha characters
        if re.search(r'[a-zA-Z]', phone_stripped):
            return False, None
        
        # Check if we have exactly 10 digits
        if len(phone_stripped) != 10:
            return False, None
        
        # Return the normalized version (digits only)
        return True, phone_stripped

    def lookup_phone_numbers(self, customer_code, phone_type=None):
        """
        Look up phone numbers for a customer from BKPHONE table.
        
        Args:
            customer_code (str): The customer code to look up
            phone_type (str, optional): Filter by phone type (P=Primary, F=Fax, etc.)
            
        Returns:
            list: List of dictionaries containing phone record information
        """
        query = f"""
        SELECT 
            BKPHONE_CSTCOD as customer_code,
            BKPHONE_PHONE as phone_number,
            BKPHONE_TYPE as phone_type,
            BKPHONE_EXT as phone_ext,
            BKPHONE_DESC as phone_desc
        FROM {self.region}.dbo.BKPHONE
        WHERE BKPHONE_CSTCOD = :customer_code
        """
        
        params = {"customer_code": customer_code}
        
        if phone_type:
            query += " AND BKPHONE_TYPE = :phone_type"
            params["phone_type"] = phone_type
        
        results = self.db.fetch(query, params)
        return results        

