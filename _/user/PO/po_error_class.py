from enum import IntEnum


class POErrorCode(IntEnum):
    """Purchase Order Error Codes"""
    
    __depends_on__ = []  # No model dependencies for error codes
    
    # Connection/Database Errors (10-29)
    MSSQL_OPEN_FAILED = 10
    MSSQL_CLOSE_FAILED = 20
    
    # Fiscal Year Errors (30-59)
    FISCAL_YEAR_IN_FUTURE = 30
    FISCAL_YEAR_IN_PAST = 40
    FISCAL_YEAR_LOAD_ERROR = 50
    
    # PO Load/Validation Errors (60-99)
    PO_LOAD_FAILED = 60
    INVALID_TO_WAREHOUSE = 70
    INVALID_FROM_WAREHOUSE = 80
    IDENTICAL_WAREHOUSE = 90
    VALIDATE_PO_FAILED = 100
    
    # PO Creation/Update Errors (110-199)
    CREATE_PO_NUMBER_FAILED = 110
    MSSQL_QUERY_FAILED = 120
    MSSQL_EXTENDED_QUERY_FAILED = 130
    FAILED_TO_LOCATE_GL_ACCT = 140
    MSSQL_INSERT_FAILED = 150
    MSSQL_UPDATE_FAILED = 160
    INVALID_PO_NUMBER = 170
    INVALID_USERNAME = 180
    INSERT_NEW_BKTRHDR_FAILED = 190
    INSERT_NEW_BKPOERD_FAILED = 191
    INSERT_NEW_BKAPPO_FAILED = 192
    
    # Warehouse/Location Errors (200-249)
    MALFORMED_TO_WAREHOUSE = 200
    MALFORMED_FROM_WAREHOUSE = 210
    FAILED_TO_LOC_LOOKUP = 220
    FAILED_PART_BIN_LOOKUP = 230
    LOCATION_LOCKED = 240
    LOAD_HUBS_FAILED = 250
    
    # PO Line/Detail Errors (260-299)
    UPDATE_HEADER_FAILED = 260
    PO_PART_FROM_FAILED = 270
    PO_PART_TO_FAILED = 280
    INSERT_NEW_BKTRLNE_FAILED = 290
    INSERT_NEW_BKAPPOL_FAILED = 291
    
    # GL/System Errors (300-349)
    FAILED_TO_FETCH_BKSYSMASTER = 290
    FAILED_TO_INSERT_BKGLTRANS = 300
    FAILED_TO_UPDATE_BKGLCOA = 310
    POST_TO_GL_FAILED = 320
    DETERMINE_COMPANY_FAILED = 330
    COMPANY_PO = 340
    FAILED_TO_DELETE_ERROR = 350
    
    # Inventory/UOO Errors (360-399)
    TO_UOO_FAILED = 360
    GET_PO_HEADER_FAILED = 370
    GET_PO_LINES_FAILED = 380
    MOVE_UBO_TO_UOH_FAILED = 390
    
    # Delete/Update Errors (400-449)
    FAILED_TO_DELETE_LINE = 400
    FAILED_TO_DELETE_HEADER = 410
    EMPTY_PO_FAILED = 420
    PRINT_PO_FAILED = 430
    UNLOCK_PO_FAILED = 430
    FAILED_TO_INSERT_HISTORY = 440
    FAILED_TO_UPDATE_HISTORY = 450
    
    # Misc Errors (450-599)
    FAILED_TO_LOAD_LINE = 460
    FAILED_TO_LOAD_PO = 470
    FAILED_TO_LOAD_AVERAGE_COST = 480
    FAILED_TO_TRACK = 490
    INSERT_PO_LOG = 500
    INVALID_AUTHTOKEN = 510
    POST2GL_ZERO = 520
    ROW_LOCK_FAILED = 530
    UPDATE_PODETAILS_FAILED = 540
    INSERT_NEW_PODETAILS_FAILED = 541
    REMOVE_UOO_FAILED = 550


# Error Messages
ERROR_MESSAGES = {
    POErrorCode.MSSQL_OPEN_FAILED: "MSSQL Failed to connect to database",
    POErrorCode.MSSQL_CLOSE_FAILED: "MSSQL Failed to close database",
    POErrorCode.MSSQL_INSERT_FAILED: "MSSQL Failed to insert a record in the database",
    POErrorCode.MSSQL_UPDATE_FAILED: "MSSQL Failed to update a record in the database",
    POErrorCode.MSSQL_QUERY_FAILED: "MSSQL Query Failed",
    POErrorCode.MSSQL_EXTENDED_QUERY_FAILED: "MSSQL Extended Query Failed",
    
    POErrorCode.FISCAL_YEAR_LOAD_ERROR: "The Fiscal year failed to load in BKSYSMSTR",
    POErrorCode.FISCAL_YEAR_IN_FUTURE: """Fiscal year cannot be in the future
*** DO NOT CHANGE THE FISCAL YEAR DATE IN SY-A ***

THE POSTING DATE IS PAST THE END OF THE FISCAL YEAR.
YOU MUST RUN YEAR END CLOSE (SY-K) BEFORE ANY POSTINGS
TO THE NEW YEAR. AFTER YOU RUN YEAR END CLOSE YOU WILL
BE ABLE TO ENTER TRANSACTIONS FOR BOTH THE OLD AND NEW
YEARS. YOU CAN RE-CLOSE THE PRIOR YEAR (SY-L) AS MANY
TIMES AS NECESSARY SO THAT ENTRIES FOR THE OLD YEAR ARE
UPDATED IN YOUR FINANCIAL STATEMENTS. PLEASE DO NOT
CHANGE THE COMPUTER DATE OR MANUALLY RESET THE FISCAL
YEAR START DATE -- DOING SO WILL CAUSE SEVERE PROBLEMS
AND WILL TAKE MANY HOURS OF WORK ON YOUR PART TO UNDO.
IF YOU HAVE ANY QUESTIONS, CALL SUPPORT FIRST.""",
    POErrorCode.FISCAL_YEAR_IN_PAST: "Fiscal year cannot be 2 years in the past. The computer's date does not fall within the valid range.",
    
    POErrorCode.COMPANY_PO: "Company PO",
    POErrorCode.DETERMINE_COMPANY_FAILED: "The Location(s) could not be pulled from the locations table",
    POErrorCode.PO_LOAD_FAILED: "The po failed to load from the database",
    POErrorCode.MALFORMED_TO_WAREHOUSE: "TO Location is EMPTY, NULL or >3 characters",
    POErrorCode.MALFORMED_FROM_WAREHOUSE: "FROM Location is EMPTY, NULL or >3 characters",
    POErrorCode.INVALID_TO_WAREHOUSE: "TO Location is not a Warehouse, does not exist, or is not active",
    POErrorCode.INVALID_FROM_WAREHOUSE: "FROM Location is not a Warehouse, does not exist, or is not active",
    POErrorCode.IDENTICAL_WAREHOUSE: "TO Location is the same as FROM Location",
    POErrorCode.CREATE_PO_NUMBER_FAILED: "Failed to get PO Number",
    POErrorCode.FAILED_TO_LOCATE_GL_ACCT: "Failed to open/locate GL Account",
    POErrorCode.FAILED_TO_INSERT_BKGLTRANS: "Failed to INSERT BKGLTRANS",
    POErrorCode.FAILED_TO_UPDATE_BKGLCOA: "Failed to UPDATE BKGLCOA",
    POErrorCode.VALIDATE_PO_FAILED: "Failed to Validate PO",
    POErrorCode.INVALID_PO_NUMBER: "The po number is invalid",
    POErrorCode.INVALID_USERNAME: "The username is invalid",
    POErrorCode.INSERT_NEW_BKPOERD_FAILED: "Failed to create BKPOERD record for the PO",
    POErrorCode.UPDATE_PODETAILS_FAILED: "Failed to update po_details record for the PO",
    POErrorCode.INSERT_NEW_PODETAILS_FAILED: "Failed to create po_details record for the PO",
    POErrorCode.INSERT_NEW_BKAPPO_FAILED: "Failed to create Header for the PO",
    POErrorCode.INSERT_NEW_BKAPPOL_FAILED: "Failed to create Line Item For PO",
    POErrorCode.FAILED_TO_LOC_LOOKUP: "Failed to query the TO LOCATION for parts",
    POErrorCode.FAILED_PART_BIN_LOOKUP: "Failed to query the PART BIN Table",
    POErrorCode.LOCATION_LOCKED: "PO Location Locked",
    POErrorCode.LOAD_HUBS_FAILED: "Failed to load HUB location data",
    POErrorCode.UPDATE_HEADER_FAILED: "Failed to update BKAPPO",
    POErrorCode.PO_PART_FROM_FAILED: "Failed to remove part from source warehouse",
    POErrorCode.PO_PART_TO_FAILED: "Failed to add part from dest warehouse",
    POErrorCode.FAILED_TO_FETCH_BKSYSMASTER: "Failed to fetch BKSYSMASTER",
    POErrorCode.FAILED_TO_DELETE_ERROR: "Failed to Delete an invalid database row",
    POErrorCode.POST_TO_GL_FAILED: "Post to GL failed",
    POErrorCode.TO_UOO_FAILED: "Move TO UOO in FROM warehouse Failed",
    POErrorCode.GET_PO_HEADER_FAILED: "Failed to get PO Header",
    POErrorCode.GET_PO_LINES_FAILED: "Failed to get PO Lines",
    POErrorCode.MOVE_UBO_TO_UOH_FAILED: "Failed to move the UBO to UOH in the FROM Warehouse",
    POErrorCode.FAILED_TO_DELETE_LINE: "Failed to delete a PO line",
    POErrorCode.FAILED_TO_DELETE_HEADER: "Failed to delete the PO header",
    POErrorCode.EMPTY_PO_FAILED: "Failed to empty the po",
    POErrorCode.PRINT_PO_FAILED: "Failed to mark the po as printed",
    POErrorCode.UNLOCK_PO_FAILED: "Failed to unlock the po to pick list state",
    POErrorCode.FAILED_TO_INSERT_HISTORY: "Failed insert the history item",
    POErrorCode.FAILED_TO_UPDATE_HISTORY: "Failed to update the history item",
    POErrorCode.FAILED_TO_LOAD_LINE: "Failed to load po line in BKAPPOL",
    POErrorCode.FAILED_TO_LOAD_PO: "Failed to load po",
    POErrorCode.FAILED_TO_LOAD_AVERAGE_COST: "Failed to load the average Cost for a part from BKICLOC",
    POErrorCode.INSERT_PO_LOG: "Failed to insert a po log in JADVDATA",
    POErrorCode.INVALID_AUTHTOKEN: "Auth Token INVALID",
    POErrorCode.POST2GL_ZERO: "POST2GL Zero dollar Amount",
    POErrorCode.ROW_LOCK_FAILED: "Failed to lock row for update",
    POErrorCode.REMOVE_UOO_FAILED: "Cannot remove units from UOO"
}


def get_error_message(code: POErrorCode, additional_info: str = "") -> str:
    """
    Get formatted error message for a given error code
    
    Args:
        code: POErrorCode enum value
        additional_info: Additional context to append to message
        
    Returns:
        Formatted error message
    """
    base_message = ERROR_MESSAGES.get(code, "Unknown error occurred")
    
    if additional_info:
        return f"{base_message}: {additional_info}"
    
    return base_message


def format_po_error(code: POErrorCode, po_number: int = None, 
                   part: str = None, location: str = None,
                   additional_info: str = "") -> str:
    """
    Format error message with PO-specific context
    
    Args:
        code: POErrorCode enum value
        po_number: PO number if applicable
        part: Part number if applicable
        location: Location if applicable
        additional_info: Additional context
        
    Returns:
        Formatted error message with context
    """
    base_message = ERROR_MESSAGES.get(code, "Unknown error occurred")
    
    context_parts = []
    if po_number:
        context_parts.append(f"PO# {po_number}")
    if part:
        context_parts.append(f"Part: {part}")
    if location:
        context_parts.append(f"Location: {location}")
    if additional_info:
        context_parts.append(additional_info)
    
    if context_parts:
        context = " - ".join(context_parts)
        return f"{base_message} [{context}]"
    
    return base_message