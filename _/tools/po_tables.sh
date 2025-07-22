#!/bin/bash

# Model generation script - just dump your list into the array

# Connection configuration
DSN='DSN=mssql-dev;UID=webuser;PWD=!w21eb1;'
CONN='PR_MSSQL'
OUTPUT='app/user/test/'

#  "JADVDATA locations s l"
#  "JADVDATA po_log s l"
#  "JADVDATA po_lock s l"
#  "JADVDATA BKZIP s l"
#  "JADVDATA _vinv_config n"
#  "JADVDATA _vinv_locs n"
#  "JADVDATA _vinv_oem_avail n"
#  "JADVDATA _virtual_inventory n"
#  "GPACIFIC BKAPHPOL s l -S BKAPPOL"
#  "GPACIFIC BKAPHPO s l -S BKAPPO"
#  "GPACIFIC _po_details n l"
#  "GPACIFIC BKAPPO s l"
#  "GPACIFIC BKAPPOL s l"
#  "GPACIFIC BKPOERD s l"
#  "GPACIFIC BKGLCOA s l -S BKGL"
#  "GPACIFIC BKICLOC s l"
#  "GPACIFIC BKSYMSTR s l -S BKSY"
#  "GPACIFIC BKGLCOA s l"    
#  "GPACIFIC BKICVNXF s l"
#  "GPACIFIC BKAPVEND s l"
#  "GPACIFIC BKARCUST s l"
#  "GPACIFIC BKPHONE s l"
#  "GPACIFIC BKSYTERM s l"
#  "GPACIFIC BKICMSTR s l"
#  "GCANADA BKAPHPO s l -S BKAPPO"
#  "GCANADA BKAPHPOL s l -S BKAPPOL"
#  "GCANADA _po_details n l"
#  "GCANADA BKAPPO s l"
#  "GCANADA BKAPPOL s l"
#  "GCANADA BKGLCOA s l -S BKGL"
#  "GCANADA BKICLOC s l"
#  "GCANADA BKPOERD s l"
#  "GCANADA BKSYMSTR s l  -S BKSY"
#  "GCANADA BKICVNXF s l"
#  "GCANADA BKAPVEND s l"
#  "GCANADA BKARCUST s l"
#  "GCANADA BKPHONE s l"
#  "GCANADA BKSYTERM s l"
#  "GCANADA BKICMSTR s l"
#   PartsTrader orders
#   PartsTrader parked_orders
#   PartsTrader parked_order_parts
#   PartsTrader repairers
#   PartsTrader requesters
#  "PartsTrader parked_orders_po"
#  "PartsTrader parked_orders_so"
#  "JADVDATA _vinv_locs n"
#  "JADVDATA _vinv_oem_avail n"
#  "JADVDATA _virtual_inventory n"
#  "PartsTrader parked_orders_po"
#  "PartsTrader parked_orders_so"
#    "JADVDATA BKMPFRGT s l"
#    "GPACIFIC BKARINV s l"
#    "GPACIFIC BKARINVL s l"
#    "GPACIFIC BKSONOTE s l"
#    "GPACIFIC BKARPR s l"
#    "GPACIFIC BKSHPVIA s l"
#    "JADVDATA BKMPFRGT s l"
#    "GCANADA BKARINV s l"
#    "GCANADA BKARINVL s l"
#    "GCANADA BKSONOTE s l"
#    "GCANADA BKARPR s l"
#    "GCANADA BKSHPVIA s l"
#    "GCANADA USER s l"
#    "GPACIFIC USER s l"
#    "GPACIFIC NEXTSO s l"
#    "GCANADA  NEXTSO s l"
#    "JADVDATA _freightExempt n"
#    "JADVDATA _pricing_blanket_stock s n"
#    "JADVDATA _pricing_parents s n"
#    "JADVDATA _oe_list_map s n"
#    "JADVDATA _cost_basis s n"
#    "JADVDATA BKPRULES s l"
#    "JADVDATA BKMPHEAD s l"
#    "JADVDATA BKMPCONT s l"#
#    "JADVDATA BKARPR s l"
#    "JADVDATA BKEXCHNG s l"
#    "JADVDATA BKARLOCP s l"
#    "JADVDATA BKARSPPC s l"
#    "JADVDATA BKICCAT s l"
#    "GPACIFIC BKARCPRC s l"
#    "GPACIFIC BKARLSTF s l"
#    "GCANADA BKARPR s l"
#    "GCANADA BKARCPRC s l"
#    "JADVDATA users_sales_reps_meta"
#    "GCANADA BKARLSTF s l"
             
#
TABLES=(
         
 )







# Process each entry
for entry in "${TABLES[@]}"; do
    # Parse the entry - read everything after database and table as remaining
    read -r database table remaining <<< "$entry"
    
    # Initialize variables
    opt_string=""
    s_option=""
    r_option=""
    
    # Check if -S option exists in the remaining string
    if [[ $remaining =~ -S[[:space:]]+([^[:space:]]+) ]]; then
        s_arg="${BASH_REMATCH[1]}"
        s_option="-S $s_arg"
        # Remove the -S option from remaining to process other options
        remaining="${remaining//-S $s_arg/}"
    fi
    
    # Check if -R option exists in the remaining string
    if [[ $remaining =~ -R[[:space:]]+([^[:space:]]+) ]]; then
        r_arg="${BASH_REMATCH[1]}"
        r_option="-R $r_arg"
        # Remove the -R option from remaining to process other options
        remaining="${remaining//-R $r_arg/}"
    fi
    
    # Process single character options
    if [[ $remaining == *"s"* ]]; then opt_string="$opt_string -s"; fi
    if [[ $remaining == *"l"* ]]; then opt_string="$opt_string -l"; fi
    if [[ $remaining == *"n"* ]]; then opt_string="$opt_string -n"; fi
    
    echo "Processing: $database.$table"
    
    # Run the command with all options including -S and -R if present
    python tools/build_models.py -d "$database" -t "$table" -o "$OUTPUT" -c "$DSN" -b "$CONN" $opt_string $s_option $r_option -N MDS_RECNUM record
    
    echo "---"
done

echo "All done!"