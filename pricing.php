<?
/**********************************************************
*    _____                  __ _____             _        * 
*   (_____ \              / __|_____ \          | |       * 
*    _____) )____  ____ _| |__ _____) )_____  __| |       * 
*   |  ____/ ___ |/ ___|_   __)  __  /(____ |/ _  |       * 
*   | |    | ____| |     | |  | |  \ \/ ___ ( (_| |       * 
*   |_|    |_____)_|     |_|  |_|   |_\_____|\____|       * 
*                                                         * 
*   Pricing Class                                         * 
*   Created By: Charles Watkins                           * 
*   Versioned from Performance Radiator session.class.php * 
*    Created By: Matt Zyskowski                           *
*   02-21-2011                                            * 
**********************************************************/
require_once "_db.php";                                   //default db settings.

class pricing{
    public function __construct($uid,$loc=false,$debug=false) {
        db::connect();
        //db::select("JADVDATA");
        
        if($uid>7000000) {
            $this->software             = 'CA';
            $this->database             ="GCanada";
        } else {
            $this->software             = 'US';
            $this->database             ="GPacific";
        }
        
        $this->ouid = $uid; //save the original custcode
        
        $pricingParent = $this->checkForPricingParent($uid);
        if($pricingParent>0) $uid = $pricingParent;
        
        $billingParent = $this->getParent($uid);
        if($billingParent == 5032165) $uid = $billingParent;  //Autozone should always use the corporate pricing
                
        $this->blanketPricing           =$this->checkForBlanketPricing($this->ouid); //Uses ouid since it associated shipper id's
        //blanketPricing Object [custCode], [singlePriceLevel], [stockLevel], [shipper], [shipperID]
        if($this->blanketPricing){
            $uid = $this->blanketPricing->custCode;     
        }
        
        $this->insAdjuster              = false;                    //Is the user an insurance adjuster
        $this->is800                    = false;                    //Is the user an insurance adjuster
        $this->isListMin                = false;
        $this->setStockLoc              = $loc;                    //Is the user an insurance adjuster
        $this->debug                    =$debug;
        $this->customer_id              =$uid;
        $this->orderTypes               =array('single','stock','container');
        //$this->dbm                      =$this->my_connect();
        $this->isLocal                  = false; //getCustData sets this value
        $this->getCustData();
        
        $this->exchangeRates            =$this->getExchangeRates();
        $this->familyPricingLevels      =$this->getFamilyPricingLevels();
        $this->distPricingLevels        =$this->getDistPricingLevels();
        $this->distStockFields          =$this->getDistPricingLevelsStockFields();
        $this->userType                 =$this->determineUserType();        //must come after faimly and dist levels..
        $this->pricingLevelRules        =$this->getPricingLevelRules();
        $exchangeRates=$this->getExchangeRates();
        
        $this->standardExchangeRate     =$exchangeRates->exchangeRate;
        $this->discountedExchangeRate   =$exchangeRates->discountedExchangeRate;                //if the customer class = A or B the discounted exchange rate is used. (For Canadian customer only.)
        
        $this->class                    ='BS';
        $this->custState                ='WA';
        
        $classAndState                  =$this->getClassAndState();
        if($classAndState){
            $this->class                    =$classAndState->class;
            $this->custState                =$classAndState->custState;
        }
        elseif($this->customer_id != 0){ 
            error_log('[AHOY] No bkarcust record for ['.$this->customer_id.']');    
        }
        
        $this->categoryDiscounts        =$this->getCategoryDiscounts();
        $this->friendlyDistBool         =$this->isFriendlyDistributor();
        
        //removed 2021-04-19
        //if($this->customer_id==1000829) {      //THIS ACCOUNT IS INACTIVE NOW
        //   $this->is800  = true;
            //error_log('is800 '.$this->ouid);
        //    if($this->database=="GCanada") $this->systemID = 'CA.CA';                
        //}
        
        if($this->customer_id==5033238){     //ABRA Corporate Account
            $this->isListMin = false; //Discontinuing program 12/7/2021
            //$this->isListMin = true;
            //error_log($this->ouid.' list min pricing triggered');
        }
        
    }
    
    /*
    function __destruct(){
        $this->my_close();
    }  
    
    function my_connect(){
            //new pdo connection
            try {
                $dsn = 'mysql:host='.MYSQL_HOST.';dbname=perfrad';
                $options = array(PDO::MYSQL_ATTR_INIT_COMMAND => 'SET NAMES utf8');
                $dbm = new PDO($dsn,MYSQL_USER,MYSQL_PASS,$options);
            } catch (PDOException $e) {
                exit ("Error {$e->getCode()}: Could not connect to the perfrad mysql database ({$e->getMessage()})");
            }
            
            return $dbm;
    }
    
    function my_close(){
       //nothing here for now
    }
    */
    
    function getMinList($part, $bsList, $category=''){
        $price = $bsList;
        
        if(in_array($category,array('HLMP','OLMP','TLMP','MIRR'))){
            //get the min list of the two
            $query = "SELECT MinValue FROM [JADVDATA].[dbo].[_oe_list_map] ".
                        "CROSS APPLY (SELECT MIN(d) MinValue FROM (VALUES ([oe]), ([lkq])) AS a(d) WHERE d > 0) A ".
                        "WHERE part = '".str_replace("'","''",$part)."'";    
        }
        else {
            //get the min list of the three
            $query = "SELECT MinValue FROM [JADVDATA].[dbo].[_oe_list_map] ".
                        "CROSS APPLY (SELECT MIN(d) MinValue FROM (VALUES ([oe]), ([eight]), ([lkq])) AS a(d) WHERE d > 0) A ".
                        "WHERE part = '".str_replace("'","''",$part)."'";
        }
        
        $row = db::fetch($query);
                
        if($row && isset($row->MinValue)){
            if($row->MinValue > 0 && $row->MinValue < $bsList){
                $logged_new_price = false;
                
                $price = $row->MinValue;
                
                //get the cost basis min margin value
                $query2 = "SELECT ROUND(CAST(([costBasis]/0.8)/0.45 as money),2) as MinMarginValue FROM [JADVDATA].[dbo].[_cost_basis] WHERE part = '".str_replace("'","''",$part)."'";
                
                $row2 = db::fetch($query2);
                if($row2 && isset($row2->MinMarginValue)){
                    //error_log($row2->MinMarginValue);
                    if($row2->MinMarginValue > 0){
                        if($row2->MinMarginValue > $price && $row2->MinMarginValue < $bsList){
                            error_log('lower list min set to minMarginValue for '.$part.' from '.$price.' to '.$row2->MinMarginValue);
                            $logged_new_price = true;
                            $price = $row2->MinMarginValue;
                        }
                        elseif($row2->MinMarginValue > $price && $row2->MinMarginValue > $bsList) {
                            error_log('lower list min set to bsList for '.$part.' from '.$price.' to '.$bsList);
                            $logged_new_price = true;
                            $price = $bsList;
                        }
                    }
                }
                
                if(!$logged_new_price){
                    error_log('lower list min set for '.$part.' from '.$bsList.' to '.$row->MinValue);    
                }
            }
            
        }
        
        return $price;
    }
    
    private function checkForBlanketPricing($ccInput) {
        $query = "SELECT [custCode], [singlePriceLevel], [stockLevel], [shipper], [shipperID] ".
                 "FROM [JADVDATA].[dbo].[_pricing_blanket_stock] WHERE custCode = '".intval($ccInput)."'";
        $row = db::fetch($query);  //custCode is primary key, max one row returned
        if($row && is_object($row) && isset($row->custCode)) {
            return $row;    
        }
        else
            return false;
    }
    
    private function checkForPricingParent($ccInput) {
        $query = "SELECT [pricingParent] FROM [JADVDATA].[dbo].[_pricing_parents] WHERE custCode = '".intval($ccInput)."'";
        $row = db::fetch($query);
        if($row && is_object($row) && isset($row->pricingParent)) {
            return $row->pricingParent;    
        }
        else
            return 0;
    }
    
    private function getParent($custCode){
        $custCode = intval($custCode);
        $db = 'GPacific'; if($custCode >= 7000000) $db = 'GCanada';
        $query = "SELECT [BKAR_PR_PARENT] as parentCode ".
                    "FROM [$db].dbo.[BKARPR] WHERE BKAR_PR_CSTCOD = '{$custCode}'";
        $custData = db::fetch($query);
        
        if($custData && isset($custData->parentCode) && $custData->parentCode > 0)
            return $custData->parentCode;
        else
            return 0;        
    }
     
    private function getFamilyPricingLevels() {
        $familyLevelPricing = array();
        
        $familyLevelPricing['ENC']   = 'J1';                                                                //default to jobber pricing
        $familyLevelPricing['AC']    = 'J1';
        $familyLevelPricing['EXH']   = 'J1';
        $familyLevelPricing['FUEL']  = 'J1';
        $familyLevelPricing['CRSH']  = 'J1';
        $familyLevelPricing['C&I']   = 'J1';
        $familyLevelPricing['OTH']   = 'J1';
        
        if(!$this->insAdjuster) {                                                                           //get the family price levels for the supplied customer code from mssql
            $query = "SELECT BKAR_CPRC_FMLY as family, BKAR_CPRC_LEVEL as level ".
                     "FROM ".$this->database.".dbo.BKARCPRC ".
                     "WHERE BKAR_CPRC_CODE = '".intval($this->customer_id)."' ORDER BY family ASC";
            $rows=db::fetchAll($query);                                                                      //execute the query
            
            if($this->debug) log::error("GetFamilyPricingLevels",$query,__class__,__function__);
            if($rows) {                                                                                   //check for resource, errors, and price row
                foreach($rows as $row) {                                                           //Set the family levels we selected to the array
                    if(trim($row->level) == '') $row->level = 'J1';
                    $familyLevelPricing[$row->family] = $row->level;
                }
            }
            
            if(count($familyLevelPricing) <= 1) {
                log::error('PRICING ERROR',"Failed to pull more than one family level pricing row for customer code: ".$this->customer_id,__class__,__function__);
            }
        }
        
        if($this->debug) log::error("GetFamilyPricingLevels",$familyLevelPricing,__class__,__function__);
        return $familyLevelPricing;
    }
    
    private function getDistPricingLevels() {
        $distPricingLevels = array();
        $query = 'SELECT BKPRULES_PLEVEL as pricing_level FROM JADVDATA.dbo.BKPRULES WHERE BKPRULES_DISTPL = 1';
        $rows = db::fetchAll($query);
        if($this->debug) log::error("getDistPricingLevels",$query,__class__,__function__);
        foreach($rows as $row) {
            $distPricingLevels[] = $row->pricing_level;
        }
        return $distPricingLevels;
    }
    
    private function getDistPricingLevelsStockFields() {
        $distPricingLevelsStockFields = array();
        $query = 'SELECT BKPRULES_PLEVEL as pricing_level, BKPRULES_STOCK as stock_field FROM JADVDATA.dbo.BKPRULES WHERE BKPRULES_DISTPL = 1';
        $result = db::query($query);
        if($this->debug) log::error("getDistPricingLevels",$query,__class__,__function__);
        while(($row = db::fetch())) {
            $distPricingLevelsStockFields[$row->pricing_level] = $row->stock_field;
        }
        return $distPricingLevelsStockFields;
    }    
   
        
   
    private function getExchangeRates() {
        $query = "SELECT TOP 1 BKEXCHNG_RATE AS exchangeRate, BKEXCHNG_DSRATE AS exchangeDSRate ".      //query for the two exchange rates
                 "FROM JADVDATA.dbo.BKEXCHNG ORDER BY BKEXCHNG_DATE DESC";
        if($this->debug) log::error("getExchangeRates",$query,__class__,__function__);
        $row = db::fetch($query);
        //db::showQueries();
        if($row) {
            return (object)array('exchangeRate'=>$row->exchangeRate,'discountedExchangeRate'=>$row->exchangeDSRate);
        }
        log::error("Exchange Rate not found, using Defaults","",__class__,__function__);
        return (object)array('exchangeRate'=>1.035,'discountedExchangeRate'=>1.015);
    }
     
    private function getOversizeFreightAmount($part){
        $query="SELECT COALESCE((SELECT [BKMP_FRGT_AMT] FROM [jadvdata].[dbo].[BKMPFRGT] WHERE BKMP_FRGT_PART = '".str_replace("'","''",$part)."'),10) as freight";   
        if($this->debug) log::error("getOversizeFreightAmount",$query,__class__,__function__);
        $row=db::fetch($query);
        if($row && isset($row->freight)){
            return $row->freight;
        }
        return 10;
    }
     
    private function getClassAndState(){
        $query="SELECT BKAR_CLASS as class, UPPER(BKAR_STATE) as custState FROM ".$this->database.".dbo.BKARCUST WHERE BKAR_CUSTCODE='".$this->customer_id."'";   
        if($this->debug) log::error("getClassAndState",$query,__class__,__function__);
        $row=db::fetch($query);
        if($row && isset($row->class)){
            return $row;
        }
        return false;
    }
     
    private function getCategoryDiscounts() {
        $discounts = array(                                                                                                         //build the default array
                        'acDiscPercInt'  => 0,                                                                          
                        'encDiscPercInt' => 0,
                        'exhDiscPercInt' => 0,
                        'fuelDiscPercInt'=> 0,
                        'mirrDiscPercInt'=> 0
                        );

        $query = "SELECT BKAR_LST_AC, BKAR_LST_ACD, BKAR_LST_ENC, BKAR_LST_ENCD, BKAR_LST_EXH, ".                                   //query to retrieve our last purchase dates and discount start dates for each part category
                 "BKAR_LST_EXHD, BKAR_LST_FUEL, BKAR_LST_FUELD, BKAR_LST_MIRR, BKAR_LST_MIRRD ".
                 "FROM ".$this->database.".dbo.BKARLSTF WHERE BKAR_LST_CODE = '".intval($this->customer_id)."'";
        if($this->debug) log::error("getCategory Discounts",$query,__class__,__function__);
        $row=db::fetch($query);
        if($row) {
            if(in_array($this->class, array('A','B','C','RS','WD','VC','B1','B2','B3'))) {                                          //some customer classes do not receive a category discount so just return the default array
                return $discounts;
            }

            $discounts['acDiscPercInt']   =$this->calcCatDiscountPerc(trim($row->BKAR_LST_AC)  ,trim($row->BKAR_LST_ACD));          //set the disocunt percentage according 
            $discounts['encDiscPercInt']  =$this->calcCatDiscountPerc(trim($row->BKAR_LST_ENC) ,trim($row->BKAR_LST_ENCD));         //to the dates for each product family
            $discounts['exhDiscPercInt']  =$this->calcCatDiscountPerc(trim($row->BKAR_LST_EXH) ,trim($row->BKAR_LST_EXHD));
            $discounts['fuelDiscPercInt'] =$this->calcCatDiscountPerc(trim($row->BKAR_LST_FUEL),trim($row->BKAR_LST_FUELD));
            $discounts['mirrDiscPercInt'] =$this->calcCatDiscountPerc(trim($row->BKAR_LST_MIRR),trim($row->BKAR_LST_MIRRD));

            return $discounts;                                                                                                      //set are completed array to the session
        }

        return false;
    }
    
    /**
     * @return array returns the last date a part was purchased for each category as well as the date a discounted was
     * started if available.
     */
    private function calcCatDiscountPerc($lastPurchaseDate, $discountStartDate) {
        $discountPerc = 0;

        if($lastPurchaseDate != '') {                                                               //Check to see if they have purchased an AC Condenser before
           if(trim($discountStartDate) != '') {                                                     //check to see if we have a discount start date
               $discountStart = strtotime($discountStartDate);                                      //convert the textual date to a timestamp
               $daysSinceDiscountStarted = round((time()-$discountStart)/86400);                    //calculate the days since the discount was started
               
               if($daysSinceDiscountStarted < 30)                                                   //calculate the discount
                   $discountPerc = 15;                                                              //change to 15
               elseif ($daysSinceDiscountStarted < 60)
                   $discountPerc = 10;                                                              //change to 10
               elseif ($daysSinceDiscountStarted < 90)
                   $discountPerc = 5;                                                               //change to 5
           }
        
           if($discountPerc == 0) {                                                                 //if our discount still equals 0 we need to check and see if it has been 180 days since their last purchase
               $lastPurchase = strtotime($lastPurchaseDate);                                        //convert the textual date to a timestamp
               $daysSinceLastPurchase = round((time()-$lastPurchase)/86400);
               
               if($daysSinceLastPurchase >= 180)                                                    //if it has been at least 180 days since their last purchase set the discount
                   $discountPerc = 15;                                                              //change to 15
           }
        }
        else                                                                                        //discount level automatically set to 30% because they have never ordered before.
           $discountPerc = 15;                                                                      //change to 15
        
        return $discountPerc;                                                                       //return the percentage to discount this part category
    }
    
    private function getPricingLevelRules() {
        $pricingRules=array();
        if(isset($this->pRules)) return $this->pRules;
        
        foreach($this->familyPricingLevels as $level){
            $query = "SELECT TOP 1 * FROM JADVDATA.dbo.BKPRULES WHERE ".                                                      //build the query to get the bkprules row
                     "BKPRULES_PLEVEL = '".str_replace("'","''",$level)."'";    
            $row = (array)db::fetch($query);                                                                                //build the query to get the bkprules row
            if($this->debug) log::error("getPricingLevelRules",$query,__class__,__function__);
            
            if($row) {
                $pricingRules[$level] =$row;                                                                    //set the pricing rules row
            } else {
                log::error('PRICING ERROR','Unable to find pricing rules for "'.$level.'" pricing level.',__class__,__function__);
                exit('FATAL ERROR: Please contact the webmaster. Unable to find pricing rules for "'.$level.'".');
            }
        }
        $this->pRules=$pricingRules;
        return $pricingRules;                                                                                           //return the pricing level rules
    }   
    
    /**
    * distributors are only allowed to view the jobber pricing if they are in the friendly distributors table
    *
    *@param integer $this->customer_id
    */
    private function isFriendlyDistributor() {
        $friendliesArr = array(1000049,1000071,1000182,1000186,1000247,1000331,1000374,1000393,1000455,1000544,1000572,1000575,1000676,1000679,1000754,1000811,1100158,1100388,1300152,1300365,1301107,1304209,1305252,1306317,1306450,1306759,1306968,1307034,1310519,1800865,1800867,1805454,1806696,1807751,1809216,1810137,1811790,1814546,1819722,1819808,1823422,2002004,2013715,2014090,2014094,2014104,2014580,2015037,2015278,2015598,2015792,2016443,2017453,2017473,2017754,2017773,2018005,2018355,2018361,2037367,2051937,2052334,2072679,2088930,2089544,2089918,3002179,3013954,3017019,3021067,3021922,3045683,3047864,3048095,3048673,3501387,3509116,3516751,3516762,3516777,3516796,3516958,3517010,3517177,3518059,3519509,3523266,3523480,3540095,3540417,3540873,3541263,3542114,3542467,3543009,3546303,3546304,3565344,3570563,3581291,5002635,5004340,5011078,5013139,5013797,5014267,6500572,7001485,7006457,7016732);
        if(in_array($this->customer_id,$friendliesArr)) {
            return true;
        }
        
        return false;
    }
    
    private function getCustData(){
        $query="SELECT TOP 1 BKZIP_WAREHOUSE,BKZIP_LOCAL,BKAR_ZIP,BKAR_COUNTRY,BKAR_PR_PARENT FROM ".$this->database.".dbo.BKARCUST JOIN ".$this->database.".dbo.BKARPR ON BKAR_PR_CSTCOD = BKAR_CUSTCODE collate database_default ";
        if($this->database == 'GCanada') {
            $query.="LEFT JOIN JADVDATA.dbo.BKZIP ON BKZIP_ZIP=BKAR_ZIP COLLATE DATABASE_DEFAULT ";
        } else {
            $query.="LEFT JOIN JADVDATA.dbo.BKZIP ON BKZIP_ZIP=LEFT(BKAR_ZIP,5) COLLATE DATABASE_DEFAULT ";
        }
        $query.="WHERE BKAR_CUSTCODE = '".intval($this->ouid)."'";
        //error_log($query);
        
        //$query='SELECT TOP 1 BKZIP_WAREHOUSE,BKAR_ZIP,BKAR_COUNTRY FROM '.$this->database.'.dbo.BKARCUST LEFT JOIN JADVDATA.dbo.BKZIP ON BKZIP_ZIP=BKAR_ZIP COLLATE DATABASE_DEFAULT WHERE BKAR_CUSTCODE = \''.intval($this->customer_id).'\'';
        if($this->debug) log::error("getCustData",$query,__class__,__function__);
                                                        
        $row=db::fetch($query);
        if($row) {
            $this->homeLoc=$row->BKZIP_WAREHOUSE;
            $this->parent=intval($row->BKAR_PR_PARENT);
            if(trim($row->BKAR_COUNTRY)==''){
                if($this->database == 'GCanada'){
                    $row->BKAR_COUNTRY = 'Canada';
                } else {
                    $row->BKAR_COUNTRY = 'USA';
                }
            }
            
            if(strtoupper($row->BKAR_COUNTRY [0]) == 'C' )  $this->country= 'CA';    
            else                                            $this->country= 'US';
            if($row->BKZIP_LOCAL=='Y')                      $this->isLocal=true;
            else                                            $this->isLocal=false;
            $this->systemID=$this->software.".".$this->country;
        } else {
            $this->country="US";
            $this->systemID=$this->software.".".$this->country;
	    }
    }
    
    private function determineUserType() {
        $userType = 'JOBBER';

        foreach($this->familyPricingLevels as $pricingLevel) {
            if(in_array($pricingLevel, $this->distPricingLevels)) {
                $userType = 'DIST';
                break;
            }
        }
        
        return $userType;
    }
    
    //get the base prices for the part
    private function getPricingRow($partNum, $vendor='') {
        $prices = array();
        //error_log('get pricing row for '.$partNum);
        $query = "SELECT TOP 1 BKMP_HEAD_PART as BKRAD_PARTNUM, * FROM JADVDATA.dbo.BKMPHEAD ".
                 "WHERE BKMP_HEAD_PART = '".str_replace("'","''",$partNum)."'";
        //error_log($query);
        $prices = (array) db::fetch($query);
        if($this->debug) log::error($query,"",__class__,__function__);
        
        if($prices && isset($prices['BKMP_HEAD_PART'])) {
            //error_log('pricing row exists');
            $prices['VENDOR']           = '';
            $prices['BKMP_HEAD_ACAN']   = 0;
            $prices['BKMP_HEAD_BCAN']   = 0;
            $prices['BKMP_HEAD_CCAN']   = 0;
            $prices['VENDOR_2']         = '';
            $prices['BKMP_HEAD_ACAN_2'] = 0;
            $prices['BKMP_HEAD_BCAN_2'] = 0;
            $prices['BKMP_HEAD_CCAN_2'] = 0;
            
            $prices['BMIN'] = min(array($prices['BKMP_HEAD_ABS'], round($prices['BKMP_HEAD_BLIST'] * .50,2)));
            //error_log('BMin: '.$prices['BMIN']);
            $query = "SELECT BKMP_CONT_VNDID as vendor, BKMP_CONT_ACAN as a_can_price, ".
                     "BKMP_CONT_BCAN as b_can_price, BKMP_CONT_CCAN as c_can_price ".
                     "FROM JADVDATA.dbo.BKMPCONT WHERE ".
                     "BKMP_CONT_PART = '".str_replace("'","''",$partNum)."' AND ";

            
            if($vendor != '')                                                                               //select a specific vendors price if requested
                $query .= "BKMP_CONT_VNDID = '".str_replace("'","''",$vendor)."' AND ";
            
            $query .= "BKMP_CONT_CCODE = '0'";                                                              //get the most recent price for the masses

            $canPrices = db::fetchAll($query);                                                                  //execute the query to fetch the container prices if available
            if($this->debug) log::error($query,"",__class__,__function__);

            if($canPrices && is_array($canPrices) && count($canPrices) > 0) {                                                    //check for resource, errors
                $i = 1;
                foreach($canPrices as $row) {                                                 //set each vendors container price found
                    if($i == 1) {
                        $prices["VENDOR"]         = $row->vendor;
                        $prices['BKMP_HEAD_ACAN'] = $row->a_can_price;
                        $prices['BKMP_HEAD_BCAN'] = $row->b_can_price;
                        $prices['BKMP_HEAD_CCAN'] = $row->c_can_price;
                    }
                    else {
                        $prices["VENDOR_{$i}"]         = $row->vendor;
                        $prices["BKMP_HEAD_ACAN_{$i}"] = $row->a_can_price;
                        $prices["BKMP_HEAD_BCAN_{$i}"] = $row->b_can_price;
                        $prices["BKMP_HEAD_CCAN_{$i}"] = $row->c_can_price;
                    }
                    $i++;
                }
            }
        }
        
        return $prices;                                                                                //return the bkmphead row of all the prices
    }
    
    /**
     *When checking for a special location price always submit the customers home location
     */
    private function getSpecialLocationPriceIfExists($partNum) {
        $price = 0;                                                                                             //default the price to return to zero
        
        //removed 2021-04-19
        //if($this->is800) return 0;  //no special location pricing for 1-800
        if($this->isListMin) return 0;  //no special location pricing list min priced body shops
        
        $query = "SELECT TOP 1 BKAR_LOCP_PRICE as price ".                                                      //query to select the part rank
                 "FROM JADVDATA.dbo.BKARLOCP ".
                 "WHERE BKAR_LOCP_LOC = '".$this->homeLoc."' ".
                 "AND BKAR_LOCP_PCODE = '{$partNum}'";
        
        $unique = db::fetch($query);
        if($this->debug) log::error($query,"",__class__,__function__);

        if($unique && isset($unique->price) && $unique->price > 0)   //if we got a valid unique price, set it
            $price = $unique->price;
        
        return $price;                                                                                          //return the price (0 or unique price)
    }
    
    /**
     * Check the uniquePriceForCustomer table for a unique price specific to that customer/ordertype/part
     *
     * @param string $partNumStr
     * @return decimal $singlePiecePriceDec
     */
    private function getUniquePriceIfExists($partNum, $orderType, $vendor='') {
        $price = 0;                                                                                                 //default the price to return to zero

        //removed 2021-04-19
        //if($this->is800) $orderType='stock';
        
        if($orderType == 'container') {
            $query = "SELECT TOP 1 BKMP_CONT_ACAN as a_can_price FROM JADVDATA.dbo.BKMPCONT ".                            //query for unique container price
                     "WHERE BKMP_CONT_PART = '".str_replace("'","''",$partNum)."' AND ";

            if($vendor != '')                                                                                       //include specific vendor it submitted
                $query .= "BKMP_CONT_VNDID = '".str_replace("'","''",$vendor)."' AND ";

            $query .= "BKMP_CONT_CCODE = '".intval($this->ouid)."'";                                                  //include the specific customer code

            $row = db::fetch($query);                                                                          //execute the query to fetch the container prices if available
            if($this->debug) log::error($query,"",__class__,__function__);
            
            if($row && isset($row->a_can_price)) {                                                           //check for resource, errors, and price row
                $price = $row->a_can_price;
            }
        }
        else {
            $query = "SELECT TOP 1 BKAR_SPP_PRICE as price ".                                                       //Query to select customer specific single or stock price
                     "FROM JADVDATA.dbo.BKARSPPC ".
                     "WHERE BKAR_SPP_CCODE = '{$this->ouid}' ".
                     "AND BKAR_SPP_TYPE = '{$orderType}' ".
                     "AND BKAR_SPP_PCODE = '{$partNum}'";
            
            $unique = db::fetch($query);
            
            if($this->debug) log::error($query,"",__class__,__function__);
            
            if($unique && isset($unique->price) && $unique->price > 0){   //if we got a valid unique price, set it
                $price = $unique->price;
            }
                
            if($price==0 && $this->ouid != $this->customer_id) {
                $query = "SELECT TOP 1 BKAR_SPP_PRICE as price ".                                                       //Query to select customer specific single or stock price
                         "FROM JADVDATA.dbo.BKARSPPC ".
                         "WHERE BKAR_SPP_CCODE = '{$this->customer_id}' ".
                         "AND BKAR_SPP_TYPE = '{$orderType}' ".
                         "AND BKAR_SPP_PCODE = '{$partNum}'";
                
                $unique = db::fetch($query);
                if($this->debug) log::error($query,"",__class__,__function__);
                
                if($unique && isset($unique->price) && $unique->price > 0) {   //if we got a valid unique price, set it
                    $price = $unique->price;    
                }
            }
        }
        
        return $price;                                                                                     //return the price (0 or unique customer price)
    }
    
    /**
     * Sets the single piece price to the floor price if single piece price is less than floor price
     *
     * @param decimal $singlePrice
     * @param decimal $floorPrice
     */
    private function invokeFloorPriceLogic($floorPrice, $singlePrice) {
        if($singlePrice < $floorPrice) return $floorPrice;
        return $singlePrice;
    }
    
    private function invokeLastBuyDatePriceLogic($partFamily, $singlePrice,  $discountPerc, $categoryDiscounts) {
        $discountPerc = 0;
        if(isset($this->categoryDiscounts[strtolower($partFamily).'DiscPercInt']))                                                //if we have the discount percentage for this product family set it
            $discountPerc = $this->categoryDiscounts[strtolower($partFamily).'DiscPercInt'];
        if($discountPerc > 0)                                                                                               //modify the single piece price to reflect the last buy date logic
            $singlePrice = $singlePrice * ((100-$discountPerc)/100);                                                        //when discount greater than 0
            return (object)array('singlePrice'=>$singlePrice, 'discountPerc'=>$discountPerc);
    }
        
    /**
     *get cat, fam, and container bool
     *
     *@param string $partNum
     */
    private function partInfo($partNum) {
        $partInfo = (object)array('cat'=>'UNKNOWN','catDesc'=>'UNKNOWN','catFamily'=>'UNKNOWN','catTable'=>'UNKNOWN', 'container'=>0);
            
        $query = "SELECT TOP 1 BKIC_CAT_CAT as cat, BKIC_CAT_DESC as catDesc, BKIC_CAT_FMLY as catFamily, ".           //query for part details that affect pricing
                 "BKIC_CAT_TABLE as catTable, container FROM JADVDATA.dbo.BKICCAT, JADVDATA.dbo.part_meta ".
                 "WHERE MDS_RECNUM > 0 AND partStr = '".str_replace("'","''",$partNum)."' AND catStr COLLATE DATABASE_DEFAULT = BKIC_CAT_CAT";
        $row=db::fetch($query);
        if($this->debug) log::error($query,"",__class__,__function__);
        if($row) {
           // log::error($row);
            $partInfo = (object)array('cat'=>'ACKT','catDesc'=>'AC Kit','catFamily'=>'AC','catTable'=>'BKACKIT', 'container'=>0);
            return $row;
            
        } else {                                                                                                              //it is probrably C & I product
            $query = "SELECT catStr as cat, category as catDesc, 'C&I' as catFamily, container FROM ".
                     "JADVDATA.dbo.part_meta WHERE partStr = '".str_replace("'","''",$partNum)."'";
            if($this->debug) log::error($query,"",__class__,__function__);
            $row=db::fetch($query);
            if(!$row) {
                return $partInfo;
            }
            
            if($row) return $row;
        }//end else
        //if($this->debug) log::error($query);                      $part->meta
        
        if(is_object($partInfo)) {
            if(isset($partInfo->container) && $partInfo->container=='1') $partInfo->container=true; 
            else $partInfo->container=false;
        } else {
            return false;   
        }
        return $partInfo;                                                                                                       //return part info with data or empty if not found
    }
      
    private function roundWithRuleOfFive($float) {
        
        $exploded = explode('.',$float);
        $pieces = end($exploded);                                                                         //explode the float value on the decimal
        
        if(isset($pieces{0}) && $pieces{0} == 5 && isset($pieces{1}) && $pieces{1} == 0 && isset($pieces{2})) {     //check to see it is an odd number
            if($pieces{2} & 1) {
                $rounded = ceil($float);
            } else {
                $rounded = floor($float);
            }
        } else {
            $rounded = round($float);
        }
        
        return $rounded;                                             
                                                       //return the rounded number
    }
     
    function basePartItem(){
        $item=array();
        $item['singlePriceDec']     =0;
        $item['singleShpPriceDec']  =0; //singleShpPriceDec will hold the single price for non WC delivered parts for those customers in the Blanket Stock Pricing program with a shipper of WC
        $item['singleListDec']      =0;
        $item['stockPriceDec']      =0;
        $item['containerVendor']    ='';
        $item['containerPriceDec']  =0;
        $item['containerVendor_2']  ='';
        $item['containerPriceDec_2']=0;
        $item['jobber']             =0;
        $item['lastBuyDateDiscPercInt'] =0;
        $item['willCallMax']        =0;
        $item['willCallPerc']       =0;
        return $item;
     }
     
     function error($data){
         return;
         echo "<pre>";
        print_r($data);   
        echo "</pre>";
     }
     
     
    /**
     * Get price based on product family level pricing
     *
     * @param string $partNumStr
     * @param array $orderTypesArr
     * @param string_type $errorStr
     */
    public function getPricesForPart($partNum, $orderType='', $vendor_id='', $ignoreSpecialPricing=false) {
        /******************************
        * Setting Default Values
        *****************************/
        $part=(object)array('part'=>$partNum,
                            'pricing'=>$this->basePartItem(),
                            'isContainer'=>false,
                            'vendorID'=>$vendor_id,
                            'orderType'=>$orderType,
                            'family'=>'',
                            'exchangeRate'=>'',
                            'category'=>'',
                            'pricingLevel'=>'J1',
                            'distPricingLevel'=>false,
                            'orderTypes'=>'',
                            'pricingRow'=>array(),
                            'pricingLevelRule'=>array()
                            );
        
        if($this->class=='BS'){
            //error_log('bodyshop');
            $part = $this->_getBodyShopPricesForPart($partNum, $orderType='', $vendor_id='', $ignoreSpecialPricing=false);
            //echo '<pre>';
            //print_r($part);
            //echo '</pre>';
        }
        else {
            if($partNum=='DEALER ITEM' || $partNum=='NON-STOCKING') return $this->basePartItem();
            
            if(array_search($orderType,$this->orderTypes )){                                                                                    //We need to make a userOrderTypesArr session variable that holds all the different pricing levels the user can view (should reflect pricing level and preference factors)
                $part->orderTypes= array($orderType);
            } else {
                $part->orderTypes= $this->orderTypes;
            }

            if($part->part == 'ANTIFREEZE') {
                $part->family   ='ENC';
                $part->category ='COOL';
            } else {
                $partInfo         =$this->partInfo($partNum);
                if(is_object($partInfo)) {
                    $part->family     =$partInfo->catFamily;
                    $part->category   =$partInfo->cat;
                    $part->isContainer=$partInfo->container;
                } else {
                    log::error("Failed to get Part Info",$partInfo,__class__,__function__);
                    $part->family     ='';
                    $part->category   ='';
                    $part->isContainer=false;   
                    
                }
                
            }
            
            //if($part->category == 'CON' || $part->category == 'FAN' || $part->category == 'RFAN') {
            //    //Condenser and Fan pricing should now be associated with the MIRR pricing level.
            //    $part->family = 'CRSH';
            //}


            if($part->category=='ACKT' || $part->category=='UNKNOWN') return $part->pricing;
          
          
            if($part->family    =='')     {
                log::error($part->part.' missing part table record<br>',
                $part,__class__,__function__);
                return $part->pricing;
            }   
            if(isset($this->familyPricingLevels[$part->family])) {
                $part->pricingLevel=$this->familyPricingLevels[$part->family];                                  //ex. D1-D5, B1-B4, J1, GP   //Determine the pricing level assigned to the part based on the customers product family pricing assignment
            }
            
            if(isset($this->familyPricingLevels['ENC']) && $this->familyPricingLevels['ENC']=='GP') {           //override any gp enc to gp for all families
                $part->pricingLevel = 'GP';
            }
            
            if(in_array($part->pricingLevel, $this->distPricingLevels)) {                                       //if distributor 
                $part->distPricingLevel = true;
            } else {
                $part->orderTypes = array('single');
            }
            
            if(isset($this->pricingLevelRules[$part->pricingLevel])) {
                $part->pricingLevelRule = $this->pricingLevelRules[$part->pricingLevel];                        //get the pricing level rules row from the bkprules table for the pricing level matched to the part
            }
            else {
                error_log('Pricing Level Rules not found for Fam:'.$part->family.' Lvl:'.$part->pricingLevel.' CC:'.$this->customer_id);
            }
                 
            $part->pricingRow=$this->getPricingRow($part->part,$part->vendorID);                                                        //get the bkmphead row for this part
            if(empty($part->pricingRow))                        return $part->pricing;

            if(isset($part->pricingRow['BKMP_HEAD_JOBBR']))    $part->pricing['jobber'] = $part->pricingRow['BKMP_HEAD_JOBBR'];
            
            $part->pricing['pricingLevelStr'] = $part->pricingLevel;
                
                                               
            /*******************************************************************************************************
            * Main LOOP for pricing Function....
            *******************************************************************************************************/
            foreach($part->orderTypes as $orderType) {                                              
                /*******************************************************************************************************
                * Check for UNIQUE PRICING!
                *******************************************************************************************************/
                $part->pricing['unique'][$orderType]=$this->getUniquePriceIfExists($part->part,$orderType,$part->vendorID);
                if($part->pricingLevel== 'D4' || $part->pricingLevel== 'D5') $part->exchangeRate = $this->discountedExchangeRate;                      //set the exhange rate to use the discounted rate if D4 or D5 pricing level
                else                                                         $part->exchangeRate = $this->standardExchangeRate;                        //just use the standard if conversion needed

                if($part->pricing['unique'][$orderType]>0 && !$ignoreSpecialPricing) {    
                    //$part->pricing['singlePriceDec'] =$part->pricing['unique'][$orderType];
                    $orderType = strtolower($orderType);
                    if($this->debug)       echo '<p>Special pricing exists for part '.$part->part.'</p>';
                   
                    switch($orderType) {
                        case 'container':   if($part->isContainer) {
                                               $part->pricing['containerVendor']   = $part->vendorID;
                                               $part->pricing['containerPriceDec'] = $part->pricing['unique'][$orderType];
                                            } 
                                            break;
                        
                        case 'stock'    :  $part->pricing['stockPriceDec']  = $part->pricing['unique'][$orderType];
                                            break;
                        
                        case 'single'   :  $part->pricing['singlePriceDec'] = $part->pricing['unique'][$orderType];
                                            
                                           $part->pricing['willCallDiscAmtDec']= $part->pricing['singlePriceDec']*$part->pricingLevelRule['BKPRULES_WCDISC'];
                                           $part->pricing['willCallMax']       = $part->pricingLevelRule['BKPRULES_WCMAX'];
                                           $part->pricing['willCallPerc']      = $part->pricingLevelRule['BKPRULES_WCDISC'];
                                           
                                           if($part->pricing['willCallDiscAmtDec']>$part->pricingLevelRule['BKPRULES_WCMAX']){   
                                               $part->pricing['willCallDiscAmtDec']=$part->pricingLevelRule['BKPRULES_WCMAX'];
                                           }
                                            
                                           if(in_array($this->customer_id, array(3678818,3543968,3596667,3013954,1819722,5032165,3668747,3697514,3628075,3680847))){
                                               $part->pricing['willCallDiscAmtDec']=0;
                                               $part->pricing['willCallMax']       =0;
                                               $part->pricing['willCallPerc']      =0;
                                           }
                                       
                                            break;
                    }//end switch
                    
                   $part->pricing['pricingLevelStr'] = 'UCP';
                }   else {
                    if(!$part->isContainer && $orderType=='container') continue;
                    
                    /*******************************************************************************************************
                    * Need to set price for blanket pricing customers with a shipper of WC who end up 
                    * getting the item from a different location
                    *******************************************************************************************************/
                    if($orderType== 'single' && $this->blanketPricing && $this->blanketPricing->shipper == 'WC') {
                       $part=$this->singlePricingDeux($part,true);    //sets price as singleShpPriceDec
                       //error_log('WC Shipped Price Fetched:'.$part->part.' is '.$part->pricing['singleShpPriceDec']);
                    }
                    
                    /*******************************************************************************************************
                    * No UniuquePrice... Fetch the requested type of price.
                    *******************************************************************************************************/
                    switch($orderType) {
                        case 'container': $part=$this->containerPricing ($part); break;
                        case 'stock'    : $part=$this->stockPricing     ($part); break;
                        case 'single'   : $part=$this->singlePricingDeux($part); break;
                    }
                }
                /*******************************************************************************************************
                * If single update list price and willcall etc...
                *******************************************************************************************************/
                if($orderType== 'single') {
                   $part=$this->determineSingleListPricing($part);
                }
            }
            
            /*******************************************************************************************************
            * Array Cleanup...
            *******************************************************************************************************/
            if($this->userType == 'DIST' && 
                (!isset($part->pricing['stockPriceDec']) || intval($part->pricing['stockPriceDec']) == 0) && isset($part->pricing['singlePriceDec'])) {
                       //error_log($part->pricing['stockPriceDec']);
                       $part->pricing['stockPriceDec'] = $part->pricing['singlePriceDec'];
                       //error_log('');
            }

            foreach ($part->pricing as $type=>$price) {
                if(!is_array($price) &&  substr($type,-3) == 'Dec') $part->pricing[$type]=number_format($price,2,'.','');
            }
            //log::error($part);
            if($this->debug) log::error($part,"",__class__,__function__);
            $this->part=$part;  
            
            //1-800 multiplier
            //removed 2021-04-19
            //if($this->is800 && isset($part->pricing['singlePriceDec']) && $part->pricing['singlePriceDec'] > 0) {
            //    $part->pricing['singlePriceDec'] = $part->pricing['singlePriceDec']*1.15;
            //    
            //    if($this->database == "GCanada")
            //        $part->pricing['singlePriceDec'] = $part->pricing['singlePriceDec'] * 1.06 * $this->discountedExchangeRate;       
            //}
            
            //HON GP Multiplier
            if($this->customer_id == 1300502){
                $part->pricing['singlePriceDec'] = ROUND($part->pricing['singlePriceDec']*1.2,2);               //10% Pricing Premium for HON GP Customers    
            }
            elseif($this->homeLoc=='HON' && $part->pricingLevel != 'GP' && $part->pricingLevel[0] != 'B'        //2.5% Pricing Premium for HON non GP/BS Customers and non RAD/CON parts
                     && !in_array($part->category,array('RAD','CON','HLMP','OLMP','TLMP','MIRR','WREG'))){
                //$part->pricing['singlePriceDec'] = ROUND($part->pricing['singlePriceDec']*1.025,2);    
                $part->pricing['singlePriceDec'] = ROUND($part->pricing['singlePriceDec']*1.04,2);    
            }
            elseif($this->custState=='AK' && $part->pricingLevel == 'GP'){                                      //10% Pricing Premium for Alaska GP Customers
                $part->pricing['singlePriceDec'] = ROUND($part->pricing['singlePriceDec']*1.1,2);    
            }
            elseif($this->custState=='AK' && $part->pricingLevel != 'GP' && $part->pricingLevel[0] != 'B'){     //5% Pricing Premium for Alaska non GP/BS Customers
                $part->pricing['singlePriceDec'] = ROUND($part->pricing['singlePriceDec']*1.05,2);    
            }
        }
        
        return $part->pricing;
    }
    
    /**
     * Get prices based on new body shop schema:
     * - variable list pricing
     * - variable platform pricing
     *
     * @param string $partNumStr
     * @param array $orderTypesArr
     * @param string_type $errorStr
     */
    private function _getBodyShopPricesForPart($partNum, $orderType='', $vendor_id='', $ignoreSpecialPricing=false) {
        /******************************
        * Setting Default Values
        *****************************/
        $part=(object)array('part'=>$partNum,
                            'pricing'=>$this->basePartItem(),
                            'isContainer'=>false,
                            'vendorID'=>$vendor_id,
                            'orderType'=>$orderType,
                            'family'=>'',
                            'exchangeRate'=>'',
                            'category'=>'',
                            'pricingLevel'=>'J1',
                            'distPricingLevel'=>false,
                            'orderTypes'=>'',
                            'pricingRow'=>array(),
                            'pricingLevelRule'=>array()
                            );
        
        if($partNum=='DEALER ITEM' || $partNum=='NON-STOCKING') return $this->basePartItem();
        
        // We only want to return single piece prices
        $part->orderTypes = array('single');

        if($part->part == 'ANTIFREEZE') {
            $part->family   ='ENC';
            $part->category ='COOL';
        } else {
            $partInfo         =$this->partInfo($partNum);
            if(is_object($partInfo)) {
                $part->family     =$partInfo->catFamily;
                $part->category   =$partInfo->cat;
                $part->isContainer=$partInfo->container;
            } else {
                log::error("Failed to get Part Info",$partInfo,__class__,__function__);
                $part->family     ='';
                $part->category   ='';
                $part->isContainer=false;   
                
            }
            
        }
        
        //if($part->category == 'CON' || $part->category == 'FAN' || $part->category == 'RFAN') {
            //Condenser and Fan pricing should now be associated with the MIRR pricing level.
        //    $part->family = 'CRSH';
        //}


        if($part->category=='ACKT' || $part->category=='UNKNOWN') return $part;
      
      
        if($part->family    =='')     {
            log::error($part->part.' missing part table record<br>',
            $part,__class__,__function__);
            return $part;
        }   
        if(isset($this->familyPricingLevels[$part->family])) {
            $part->pricingLevel=$this->familyPricingLevels[$part->family];                                  //ex. D1-D5, B1-B4, J1, GP   //Determine the pricing level assigned to the part based on the customers product family pricing assignment
        }
        
        if(isset($this->pricingLevelRules[$part->pricingLevel])) {
            $part->pricingLevelRule = $this->pricingLevelRules[$part->pricingLevel];                        //get the pricing level rules row from the bkprules table for the pricing level matched to the part
        }
        else {
            error_log('Pricing Level Rules not found for Fam:'.$part->family.' Lvl:'.$part->pricingLevel.' CC:'.$this->customer_id);
        }
             
        $part->pricingRow=$this->getPricingRow($part->part,$part->vendorID);                                                        //get the bkmphead row for this part
        if(empty($part->pricingRow))                        return $part;

        if(isset($part->pricingRow['BKMP_HEAD_JOBBR']))    $part->pricing['jobber'] = $part->pricingRow['BKMP_HEAD_JOBBR'];
        
        $part->pricing['pricingLevelStr'] = $part->pricingLevel;
        
        /*******************************************************************************************************
        * Main LOOP for pricing Function....
        *******************************************************************************************************/
        foreach($part->orderTypes as $orderType) {                                              
            /*******************************************************************************************************
            * Check for UNIQUE PRICING!
            *******************************************************************************************************/
            $part->pricing['unique'][$orderType]=$this->getUniquePriceIfExists($part->part,$orderType,$part->vendorID);
            if($part->pricingLevel== 'D4' || $part->pricingLevel== 'D5') $part->exchangeRate = $this->discountedExchangeRate;                      //set the exhange rate to use the discounted rate if D4 or D5 pricing level
            else                                                         $part->exchangeRate = $this->standardExchangeRate;                        //just use the standard if conversion needed

            if($part->pricing['unique'][$orderType]>0 && !$ignoreSpecialPricing) {    
                //$part->pricing['singlePriceDec'] =$part->pricing['unique'][$orderType];
                $orderType = strtolower($orderType);
                if($this->debug)       echo '<p>Special pricing exists for part '.$part->part.'</p>';
               
                switch($orderType) {
                    case 'single'   :  $part->pricing['singlePriceDec'] = $part->pricing['unique'][$orderType];
                                        
                                       $part->pricing['willCallDiscAmtDec']= $part->pricing['singlePriceDec']*$part->pricingLevelRule['BKPRULES_WCDISC'];
                                       $part->pricing['willCallMax']       = $part->pricingLevelRule['BKPRULES_WCMAX'];
                                       $part->pricing['willCallPerc']      = $part->pricingLevelRule['BKPRULES_WCDISC'];
                                       
                                       if($part->pricing['willCallDiscAmtDec']>$part->pricingLevelRule['BKPRULES_WCMAX']) {   
                                           $part->pricing['willCallDiscAmtDec']=$part->pricingLevelRule['BKPRULES_WCMAX'];
                                       }
                                        
                                       if(in_array($this->customer_id, array(3678818,3543968,3596667,3013954,1819722,5032165,3668747,3697514,3628075,3680847))){
                                           $part->pricing['willCallDiscAmtDec']=0;
                                           $part->pricing['willCallMax']       =0;
                                           $part->pricing['willCallPerc']      =0;
                                       }
                                       
                                       break;
                }//end switch
                
               $part->pricing['pricingLevelStr'] = 'UCP';
            }   else {
                if(!$part->isContainer && $orderType=='container') continue;
                /*******************************************************************************************************
                * No UniuquePrice... Fetch the requested type of price.
                *******************************************************************************************************/
                switch($orderType) {
                    case 'single'   : $part=$this->singleBodyShopPricingDeux($part); break;
                }
            }
            /*******************************************************************************************************
            * If single update list price and willcall etc...
            *******************************************************************************************************/
            if($orderType== 'single') {
               $part=$this->determineSingleListPricing($part);
            }
        }
        
        /*******************************************************************************************************
        * Array Cleanup...
        *******************************************************************************************************/
        foreach ($part->pricing as $type=>$price) {
            if(!is_array($price) &&  substr($type,-3) == 'Dec') $part->pricing[$type]=number_format($price,2,'.','');
        }
        //log::error($part);
        if($this->debug) log::error($part,"",__class__,__function__);
        $this->part=$part;  
        
        
        return $part;
    } 
        
    function showPartData(){
        log::error("SystemID:".$this->systemID,"",__class__,__function__);
        log::error("Home Loc:".$this->homeLoc,"",__class__,__function__);
        log::error($this->part,"",__class__,__function__);
    }
    
    
    function singlePricingDeux($part, $shippedBlanketWC = false){  
        if($this->debug) echo '<p><b>CALCULATING SINGLE PRICE</b></p>';
        
        $part->pricingRowField=$part->pricingLevelRule['BKPRULES_SINGLE'];                                                                      //set the bkmp head field
        
        if(isset($part->pricingRow['BMIN'])){
            $BMin = $part->pricingRow['BMIN'];
        }
        else {
            //error_log('NO BMIN for part '.$part->part);
        }
        
        if(in_array($this->customer_id, array(3678818,3543968,3596667,3013954))) { $part->pricingRowField = 'EXH'; }   //Single piece override for D1 stock single customer GWC, RadEx, US Auto
        if(in_array($this->customer_id, array(1819722,3668747,3697514,3628075,3680847))) { $part->pricingRowField = 'WD2'; } //Single piece override for D2 Stock single customer Unlimited
        if(in_array($this->customer_id, array(5032165))) { $part->pricingRowField = 'WD2'; } //Was CFILL //Single piece override for D3 stock single customer Autozone
        
        $part->pricing['singleListDec']= 0;
        $part->pricing['willCallDiscAmtDec'] = 0;
        
        //1-800 uses the stock price field.
        //removed 2021-04-19
        //if($this->is800) {
        //    $part->pricingRowField =$part->pricingLevelRule['BKPRULES_STOCK'];
        //    //error_log('using ABFILL for 800 single '.$part->pricingRowField);
        //    if($part->pricingRowField=='ABFILL') $part->pricingRowField='ABFIL';
        //}
        
        //blanket pricing trumps all but unique prices
        if($this->blanketPricing && !$shippedBlanketWC){
            $part->pricingRowField = $this->distStockFields[$this->blanketPricing->singlePriceLevel];
            if($part->pricingRowField=='ABFILL') $part->pricingRowField='ABFIL';            
        }
        
        if($part->pricingLevel== 'J1' && !in_array($this->customer_id, array(3678818,3543968,3596667,3013954,1819722,5032165,3668747,3697514,3628075,3680847)) && !$this->blanketPricing) {
            $price= $this->getSpecialLocationPriceIfExists($part->part);
            if($price && $price>0)  {
                $part->pricing['singlePriceDec']=$price;
                $part->pricingLevel= 'SLP';
                $part->pricing['willCallDiscAmtDec'] = $part->pricing['singlePriceDec'] * $part->pricingLevelRule['BKPRULES_WCDISC'];
                $part->pricing['willCallMax']        = $part->pricingLevelRule['BKPRULES_WCMAX'];
                $part->pricing['willCallPerc']       = $part->pricingLevelRule['BKPRULES_WCDISC'];
                                           
                if($part->pricing['willCallDiscAmtDec'] > $part->pricingLevelRule['BKPRULES_WCMAX']) 
                   $part->pricing['willCallDiscAmtDec'] = $part->pricingLevelRule['BKPRULES_WCMAX'];
                
                return $part;
            }
        }
        
        if(isset($part->pricingRow['BKMP_HEAD_'.$part->pricingRowField])) {
            if($shippedBlanketWC){
                $part->pricing['singleShpPriceDec']= $part->pricingRow['BKMP_HEAD_'.$part->pricingRowField];                                           //set the price for the part
            } 
            else {
                $part->pricing['singlePriceDec']= $part->pricingRow['BKMP_HEAD_'.$part->pricingRowField];                                           //set the price for the part
            }
        
            if($part->pricingLevel== 'J1' && $this->homeLoc == 'ANC') {
                $part->pricing['singlePriceDec'] = ROUND($part->pricing['singlePriceDec'] * 1.05,2);
            }
        }
        
        //if($this->homeLoc == 'HON' && in_array($part->category,array('HLMP','OLMP','TLMP','MIRR','WREG'))){
        //    $part->pricing['pricingLevelStr'] = 'B3';
        //    $part->pricingLevelRule['BKPRULES_LIST']='BLIST';    
        //}
        
        if(in_array($part->pricing['pricingLevelStr'],array('B1','B3'))){
            //error_log('HON PR* indeed core BMIN Base Price: '.$BMin.' Home Loc: '.$this->homeLoc);
            //error_log('HON PR* indeed core BKPRULES LIST Field: '.$part->pricingLevelRule['BKPRULES_LIST']);
            
            if($part->pricingLevelRule['BKPRULES_LIST']== 'BLIST' && $this->systemID == 'CA.CA') {
                $BMin = $BMin * $part->exchangeRate * floatval($part->pricingLevelRule['BKPRULES_CANFAC']);
            }
            
            //error_log('HON PR* BMIN Base Price: '.$BMin);
            $part->pricing['singlePriceDec'] = $BMin;
            
            $freight = 0;
            if(!$this->isLocal){
                $freight = $this->getOversizeFreightAmount($part->part);    
                //error_log('not local adding freight '.$freight);
            }
            
            $list_factor = 0.75; //PR1/B1
                        
            $part->pricing['singlePriceDec'] += $freight;
            //error_log('HON PR* '.$part->pricing['pricingLevelStr'].' '.$part->part.' Price  '.$part->pricing['singlePriceDec']);
            
            $part->pricing['singleListDec'] = round($part->pricing['singlePriceDec'] / $list_factor,2);
            
            if($part->pricing['pricingLevelStr'] == 'B3'){
                $part->pricing['singlePriceDec']  = round($part->pricing['singleListDec'] * 0.7,2); //PR3/B3
            }
            //error_log('HON PR* '.$part->pricing['pricingLevelStr'].' '.$part->part.' List  '.$part->pricing['singleListDec']);
        }
        
        if($part->pricingLevelRule['BKPRULES_LIST']=='BLIST'){
            if($this->isListMin){
                $part->pricing['singlePriceDec'] = $this->getMinList($part->part,$part->pricing['singlePriceDec'],$part->category);
            }
            
            elseif($this->custState == 'AK') {
                $part->pricing['singlePriceDec'] = ROUND($part->pricing['singlePriceDec'] * 1.06,2);  
            }
            
            if(!in_array($part->pricing['pricingLevelStr'],array('B1','B3'))){  
                $part->pricing['singleListDec']= $part->pricing['singlePriceDec'];                                                                  //if B1-B4 the base list price for us is simple
            }
        }
        
        if($part->pricingLevelRule['BKPRULES_LIST']== 'BLIST' && $this->systemID == 'CA.CA') {                                                          //modify the start price if a body shop in canada
            if(!in_array($part->pricing['pricingLevelStr'],array('B1','B3'))){
                if($this->debug)   echo "<br><b>Modifying base body shop list price of ".$part->pricing['singlePriceDec']." US to canadian dollars w/duty.</b>";
                $part->pricing['singleListDec']   = $part->pricing['singlePriceDec'] * 
                                                    $part->exchangeRate * 
                                                    floatval($part->pricingLevelRule['BKPRULES_CANFAC']);                                           //calcuate the list price for canada by multiplying the BLIST price by the exchange rate and duty percentage
                $part->pricing['singlePriceDec'] = $part->pricing['singleListDec'];                                                                                                   //now set the single price equal to the list price so we only have to multiply it by the single factor.
            }
        }     
        
        if(!in_array($part->pricing['pricingLevelStr'],array('B1','B3')) && $part->pricingLevelRule['BKPRULES_SINGLF'] > 0) {                                                                                      //multiply by the single piece modifier if exists
            if($this->debug) echo "<br><b>Invoking single piece modifier on ".$part->pricing['singlePriceDec']." of ".$part->pricingLevelRule['BKPRULES_SINGLF'].".</b>";
            $part->pricing['singlePriceDec'] *= $part->pricingLevelRule['BKPRULES_SINGLF'];
        }      
         
             
        
        if($part->pricingLevelRule['BKPRULES_BDATEL'] == 1) {                                                                                     //if this pricing level invokes the last buy date discount logic modify the price accordingly
            if($this->debug)   echo "<br><b>Invoking last buy date logic on ".$part->pricing['singlePriceDec'].".</b>";
            $logic=$this->invokeLastBuyDatePriceLogic($part->family,$part->pricing['singlePriceDec'], $this->debug, $part->pricing['lastBuyDateDiscPercInt']);
            
            $part->pricing['lastBuyDateLogic'] =$part->pricing['singlePriceDec'];
            $part->pricing['singlePriceDec']   =$logic->singlePrice;
            $lastBuyDateDiscPercInt =$logic->discountPerc;
            if($part->pricing['lastBuyDateLogic'] != $part->pricing['singlePriceDec']) {
                $part->pricing['lastBuyDateLogic'] .= '=>'.$part->pricing['singlePriceDec'];
            } else {
                $part->pricing['lastBuyDateLogic'] = '';
            }
            $part->pricing['lastBuyDateDiscPercInt'] = $lastBuyDateDiscPercInt;
        }  
                                                     
        //removed 2021-04-19
        //if(!$this->is800 && $part->pricingLevelRule['BKPRULES_FLOOR'] == 1) {                                                                                   //if this pricing level invokes the floor price logic modify the price accordingly
        if($part->pricingLevelRule['BKPRULES_FLOOR'] == 1) {                                                                                   //if this pricing level invokes the floor price logic modify the price accordingly
            if($this->debug) echo "<br><b>Invoking floor logic on ".$part->pricing['singlePriceDec'].".</b>";
            $part->pricing['floorLogic'] = $part->pricing['singlePriceDec'];
            if(isset($part->pricingRow['BKMP_HEAD_FLOOR'])) {
                $part->pricing['floorPriceDec']  =$part->pricingRow['BKMP_HEAD_FLOOR'];
                $part->pricing['singlePriceDec'] =$this->invokeFloorPriceLogic($part->pricing['floorPriceDec'],$part->pricing['singlePriceDec']);
            }

            if($part->pricing['floorLogic'] != $part->pricing['singlePriceDec']) $part->pricing['floorLogic'] .= '=>'.$part->pricing['singlePriceDec'];
            else                                                                 $part->pricing['floorLogic'] = '';
        }
        
        if($this->debug) echo '<p><b>Reaching ca ex rate mod</b></p>';
        
        if($this->systemID == 'CA.CA' && $part->pricingLevelRule['BKPRULES_SINGLE'] != 'BLIST') {       //check to see if the software to country is ca.ca, if so add modifier and multiplying by ex. rate and ca factor//we do not need to do this for body shops because we already factored it in.
            if($this->debug) {
                echo '<p><b>convert to ca dollars from '.$part->pricing['singlePriceDec'].'</b></p>';
                echo "<p>(S:".$part->pricing['singlePriceDec']." * E:".$part->exchangeRate." * ".
                        $part->pricingLevelRule['BKPRULES_CANFAC'].") + ".$part->pricingLevelRule['BKPRULES_CANSUR']."</p>";
            }
            $part->pricing['singlePriceDec'] = ($part->pricing['singlePriceDec'] * $part->exchangeRate * $part->pricingLevelRule['BKPRULES_CANFAC']) + $part->pricingLevelRule['BKPRULES_CANSUR'];
        } elseif($this->systemID == 'US.CA')                                                             //check to see if the software to country is us.ca, if so add modifier and exchange rate for stock price anddivide by exchange rate
            $part->pricing['singlePriceDec'] = (($part->pricing['singlePriceDec'] * $part->exchangeRate * $part->pricingLevelRule['BKPRULES_CANFAC']) + $part->pricingLevelRule['BKPRULES_CANSUR']) / $part->exchangeRate;
        
        //Lamp prices in canada need to be 90% of final price calculated.    
        if($this->systemID == 'CA.CA' && in_array($part->category, array('HLMP','TLMP','OLMP'))){
            $part->pricing['singlePriceDec'] = round($part->pricing['singlePriceDec'] * 0.90,2);   
        }
        //Condenser prices in canada need to be 95% of final price calculated.    
        if($this->systemID == 'CA.CA' && in_array($part->category, array('CON'))){
            //$part->pricing['singlePriceDec'] = round($part->pricing['singlePriceDec'] * 0.95,2);   
        }
                
        if($part->pricing['singlePriceDec'] > 0) {
            $part->pricing['willCallDiscAmtDec'] = $part->pricing['singlePriceDec'] * $part->pricingLevelRule['BKPRULES_WCDISC'];
            $part->pricing['willCallMax']        = $part->pricingLevelRule['BKPRULES_WCMAX'];
            $part->pricing['willCallPerc']       = $part->pricingLevelRule['BKPRULES_WCDISC'];
                                       
            if($part->pricing['willCallDiscAmtDec'] > $part->pricingLevelRule['BKPRULES_WCMAX']) 
               $part->pricing['willCallDiscAmtDec'] = $part->pricingLevelRule['BKPRULES_WCMAX'];
               
            if(in_array($this->customer_id, array(3678818,3543968,3596667,3013954,1819722,5032165,3668747,3697514,3628075,3680847,3683373)) || $this->blanketPricing){
                $part->pricing['willCallDiscAmtDec'] = 0;
                $part->pricing['willCallMax']        = 0;
                $part->pricing['willCallPerc']       = 0;
            }
        }  else {
            $part->pricing['willCallDiscAmtDec']=0;
        }
        
        if($part->pricingLevelRule['BKPRULES_SINGLE'] != 'BLIST'){
            //error_log('SINGLE '.$part->part.': '.$part->pricing['singlePriceDec']);
            //error_log('LIST '.$part->part.': '.$part->pricing['singleListDec']);
        }
          
        return $part;
    }
    function singleBodyShopPricingDeux($part){ 
        //error_log('singleBodyShopPricingDeux '.$part->part); 
        if($this->debug) echo '<p><b>CALCULATING SINGLE PRICE</b></p>';
        
        $part->pricingRowField=$part->pricingLevelRule['BKPRULES_SINGLE'];                                                                      //set the bkmp head field
        $part->pricing['singleListDec']= 0;                                                                                                                //Set the base list prices
        $part->pricing['willCallDiscAmtDec'] = 0;
        
        if(isset($part->pricingRow['BKMP_HEAD_'.$part->pricingRowField])) {
            $part->pricing['singlePriceDec']= $part->pricingRow['BKMP_HEAD_'.$part->pricingRowField];                                           //set the price for the part
            #New variable list pricing for body shops
            $BMin = $part->pricingRow['BMIN'];
        }
        else {
            error_log('No pricing for '.$part->part);
        }
        
        //if($this->customer_id==3561173){
        //    error_log('in bs pricing'); 
        //}
            
        
        
        
                
        
        //error_log('pricingLevelStr '.$part->pricing['pricingLevelStr']);
        //error_log('exchangeRate '.$part->exchangeRate);
        //error_log('canFactor '.$part->pricingLevelRule['BKPRULES_CANFAC']);
        //if($this->homeLoc == 'HON' && in_array($part->category,array('HLMP','OLMP','TLMP','MIRR','WREG'))){
        //    $part->pricing['pricingLevelStr'] = 'B3';    
        //}
        
        if(in_array($part->pricing['pricingLevelStr'],array('B1','B3'))){
            error_log('BS PR* indeed core BMIN Base Price: '.$BMin.' Home Loc: '.$this->homeLoc);
            error_log('BS PR* indeed core BKPRULES LIST Field: '.$part->pricingLevelRule['BKPRULES_LIST']);
            
            if($part->pricingLevelRule['BKPRULES_LIST']== 'BLIST' && $this->systemID == 'CA.CA') {
                $BMin = $BMin * $part->exchangeRate * floatval($part->pricingLevelRule['BKPRULES_CANFAC']);
            }
            
            //error_log('BS PR* BMIN Base Price: '.$BMin);
            $part->pricing['singlePriceDec'] = $BMin;
            
            $freight = 0;
            if(!$this->isLocal){
                $freight = $this->getOversizeFreightAmount($part->part);    
                error_log('not local adding freight '.$freight);
            }
            
            $list_factor = 0.75; //PR1/B1
            
            $part->pricing['singlePriceDec'] += $freight;
            error_log('BS PR* '.$part->pricing['pricingLevelStr'].' '.$part->part.' Price  '.$part->pricing['singlePriceDec']);
            
            $part->pricing['singleListDec'] = round($part->pricing['singlePriceDec'] / $list_factor,2);
            
            error_log('BS PR* '.$part->pricing['pricingLevelStr'].' '.$part->part.' List  '.$part->pricing['singleListDec']);
            
            if($part->pricing['pricingLevelStr'] == 'B3'){
                $part->pricing['singlePriceDec'] = round($part->pricing['singleListDec'] * 0.7,2); //PR3/B3
            }            
        }
            
        if($part->pricingLevelRule['BKPRULES_LIST']=='BLIST'){
            if($this->isListMin){ //I don't think this is used at all anymore
                $part->pricing['singlePriceDec'] = $this->getMinList($part->part,$part->pricing['singlePriceDec'],$part->category);
            }
                        
            if($this->custState == 'AK') {
                $part->pricing['singlePriceDec'] = ROUND($part->pricing['singlePriceDec'] * 1.06,2);  
            }
             
            if(!in_array($part->pricing['pricingLevelStr'],array('B1','B3'))){
                $part->pricing['singleListDec']= $part->pricing['singlePriceDec'];
            }                                                                  
            
        }
        
        if($part->pricingLevelRule['BKPRULES_LIST']== 'BLIST' && $this->systemID == 'CA.CA') {                                                          //modify the start price if a body shop in canada
            if(!in_array($part->pricing['pricingLevelStr'],array('B1','B3'))){
                if($this->debug)   echo "<br><b>Modifying base body shop list price of ".$part->pricing['singlePriceDec']." US to canadian dollars w/duty.</b>";
                $part->pricing['singleListDec']   = $part->pricing['singlePriceDec'] * 
                                                    $part->exchangeRate * 
                                                    floatval($part->pricingLevelRule['BKPRULES_CANFAC']);                                           //calcuate the list price for canada by multiplying the BLIST price by the exchange rate and duty percentage
                $part->pricing['singlePriceDec'] = $part->pricing['singleListDec'];                                                                                                   //now set the single price equal to the list price so we only have to multiply it by the single factor.
            }
        }     
        
        
       
        //Body Shop percentage of list price pricing
        if(!in_array($part->pricing['pricingLevelStr'],array('B1','B3')) && $part->pricingLevelRule['BKPRULES_SINGLF'] > 0) {                                                                                      //multiply by the single piece modifier if exists
            if($this->debug) echo "<br><b>Invoking single piece modifier on ".$part->pricing['singlePriceDec']." of ".$part->pricingLevelRule['BKPRULES_SINGLF'].".</b>";
            $part->pricing['singlePriceDec'] *= $part->pricingLevelRule['BKPRULES_SINGLF'];
        }      
         
        if($this->debug) echo '<p><b>Reaching ca ex rate mod</b></p>';
        
        if($this->systemID == 'CA.CA' && $part->pricingLevelRule['BKPRULES_SINGLE'] != 'BLIST') {       //check to see if the software to country is ca.ca, if so add modifier and multiplying by ex. rate and ca factor//we do not need to do this for body shops because we already factored it in.
            if($this->debug) {
                echo '<p><b>convert to ca dollars from '.$part->pricing['singlePriceDec'].'</b></p>';
                echo "<p>(S:".$part->pricing['singlePriceDec']." * E:".$part->exchangeRate." * ".
                        $part->pricingLevelRule['BKPRULES_CANFAC'].") + ".$part->pricingLevelRule['BKPRULES_CANSUR']."</p>";
            }
            $part->pricing['singlePriceDec'] = ($part->pricing['singlePriceDec'] * $part->exchangeRate * $part->pricingLevelRule['BKPRULES_CANFAC']) + $part->pricingLevelRule['BKPRULES_CANSUR'];
        } elseif($this->systemID == 'US.CA')                                                             //check to see if the software to country is us.ca, if so add modifier and exchange rate for stock price anddivide by exchange rate
            $part->pricing['singlePriceDec'] = (($part->pricing['singlePriceDec'] * $part->exchangeRate * $part->pricingLevelRule['BKPRULES_CANFAC']) + $part->pricingLevelRule['BKPRULES_CANSUR']) / $part->exchangeRate;
        
        //Lamp prices in canada need to be 90% of final price calculated.    
        if($this->systemID == 'CA.CA' && in_array($part->category, array('HLMP','TLMP','OLMP'))){
            $part->pricing['singlePriceDec'] = round($part->pricing['singlePriceDec'] * 0.90,2);   
        }
        //Condenser prices in canada need to be 95% of final price calculated.    
        if($this->systemID == 'CA.CA' && in_array($part->category, array('CON'))){
            //$part->pricing['singlePriceDec'] = round($part->pricing['singlePriceDec'] * 0.95,2);   
        }
                
        if($part->pricing['singlePriceDec'] > 0) {
            $part->pricing['willCallDiscAmtDec'] = $part->pricing['singlePriceDec'] * $part->pricingLevelRule['BKPRULES_WCDISC'];
            $part->pricing['willCallMax']        = $part->pricingLevelRule['BKPRULES_WCMAX'];
            $part->pricing['willCallPerc']       = $part->pricingLevelRule['BKPRULES_WCDISC'];
                                       
            if($part->pricing['willCallDiscAmtDec'] > $part->pricingLevelRule['BKPRULES_WCMAX']) 
               $part->pricing['willCallDiscAmtDec'] = $part->pricingLevelRule['BKPRULES_WCMAX'];

			if(in_array($this->customer_id, array(3678818,3543968,3596667,3013954,1819722,5032165,3668747,3697514,3628075,3680847,3683373)) || $this->blanketPricing){
                $part->pricing['willCallDiscAmtDec'] = 0;
                $part->pricing['willCallMax']        = 0;
                $part->pricing['willCallPerc']       = 0;
            }

        }  else {
            $part->pricing['willCallDiscAmtDec']=0;
        }
        
        return $part;
    }
    
    function containerPricing($part){
        if($this->debug) echo '<p><b>CALCULATING CONTAINER PRICE</b></p>';
        if($part->pricingLevelRule['BKPRULES_CONT']== '')   {
            if($this->debug) echo '<p><b>Container Pricing Not Available</b></p>';
            return $part;
        }
        $part->pricingRowField                = $part->pricingLevelRule['BKPRULES_CONT'];                                                  //set the bkmp head field
        $part->pricing['containerVendor']     = $part->pricingRow['VENDOR'];                                                                //set the price for the part
        $part->pricing['containerPriceDec']   = $part->pricingRow['BKMP_HEAD_'.$part->pricingRowField];
        $part->pricing['containerVendor_2']   = $part->pricingRow['VENDOR_2'];
        $part->pricing['containerPriceDec_2'] = $part->pricingRow['BKMP_HEAD_'.$part->pricingRowField.'_2'];
        if($this->debug)                        echo '<p>Actual price: '.$part->pricing['containerPriceDec'].'</p>';
        return $part;
    }
             
    function stockPricing($part){
        if($this->class == 'IC') {
            $loc = 'TAC';
            
            if($this->setStockLoc) $loc = $this->setStockLoc;   
        
            //if($this->customer_id == '7004677') $loc = 'WIN';
            $part->pricing['stockPriceDec'] = $this->getAvgcForPart($part->part,$loc);
        }
        else {
            if($this->debug) echo "Ex Rates - std: ".$this->standardExchangeRate." disc: ".$this->discountedExchangeRate;
            if($part->pricingLevelRule['BKPRULES_STOCK'] == '') {
                if($this->debug) echo "Stock Pricing Not Available";
                return $part;   
            }
           
            if($this->debug)   echo '<p><b>CALCULATING STOCK PRICE</b></p>';
            
            $part->pricingRowField =$part->pricingLevelRule['BKPRULES_STOCK'];
                        
            //blanket pricing trumps all but unique prices
            if($this->blanketPricing){
                //error_log('blanket pricing '.$this->blanketPricing->stockLevel);
                $part->pricingRowField = $this->distStockFields[$this->blanketPricing->stockLevel];            
            }
            
            if($part->pricingRowField=='ABFILL') $part->pricingRowField='ABFIL';

            $part->pricing['stockPriceDec'] =$part->pricingRow['BKMP_HEAD_'.$part->pricingRowField];                                            //set the price for the part
            
            if($this->systemID == 'CA.CA')                                                                                        //check to see if the software to country is ca.ca, if so multiply by modifier and exchange rate for stock price
                $part->pricing['stockPriceDec']= $part->pricing['stockPriceDec']* $part->pricingLevelRule['BKPRULES_CANFAC'] * $part->exchangeRate;

            //Lamp prices in canada need to be 90% of final price calculated.    
            if($this->systemID == 'CA.CA' && in_array($part->category, array('HLMP','TLMP','OLMP'))){
                $part->pricing['stockPriceDec'] = round($part->pricing['stockPriceDec'] * 0.90,2);   
            }
            //Condenser prices in canada need to be 95% of final price calculated.
            if($this->systemID == 'CA.CA' && in_array($part->category, array('CON'))){
                //$part->pricing['stockPriceDec'] = round($part->pricing['stockPriceDec'] * 0.95,2);   
            }
                
            if($part->pricingLevelRule['BKPRULES_RNDSTP'] == 1 && 
                floatval($part->pricing['stockPriceDec']) >= $part->pricingLevelRule['BKPRULES_RNDBEL'])                                        //round the stock cost of bool set
                $part->pricing['stockPriceDec'] = $this->roundWithRuleOfFive($part->pricing['stockPriceDec']);

            $part->pricing['stockPriceDec']= $part->pricing['stockPriceDec'];                                                                                    //set the price to our return array
            if($this->debug)   echo '<p>Actual price: '.$part->pricing['stockPriceDec'].'</p>';
        }

        return $part;
    }
    
    function getAvgcForPart($part, $loc) {
        if(in_array($loc, array('COQ','EDM','VAN','WIN')))
            $dbc = 'GCanada';
        else 
            $dbc = 'GPacific'; 
        
        $avgc = 1;
        $query = "SELECT BKIC_LOC_AVGC as avgc FROM {$dbc}.dbo.BKICLOC ".
                 "WHERE BKIC_LOC_PROD = '".str_replace("'","''",$part)."' AND BKIC_LOC_CODE = '".str_replace("'","''",$loc)."'";
        $row = db::fetch($query);
        if($row && isset($row->avgc)) {
            $avgc = $row->avgc;
        }
        
        if($avgc <= 1) $avgc = 1;  //set the avgc to something that can be added to the cart if it is invalid
        
        return $avgc;
    }
    

     function determineSingleListPricing($part){
        //if($this->homeLoc == 'HON' && in_array($part->category,array('HLMP','OLMP','TLMP','MIRR','WREG'))){
        //    //error_log('HON LIST ALREADY COMPLETE');
        //    return $part;
        //}
        if($part->pricingLevelRule['BKPRULES_SINGLE'] != 'BLIST') {
            $part->pricing['singleListDec'] = $part->pricingRow['BKMP_HEAD_BLIST'];
            
            if($this->systemID == 'CA.CA') {
                $part->pricing['singleListDec'] = $part->pricing['singleListDec'] * $part->exchangeRate;
            }
        }
        
        
        
        /* 
        if($part->pricingLevelRule['BKPRULES_LIST'] == 'NET' && isset($part->pricingRow['BKMP_HEAD_JOBBR'])) {                                  //if we need to apply the NET logic to the list price
            $part->pricing['compareToJobberListDec']= $part->pricingRow['BKMP_HEAD_JOBBR'];
            if($this->systemID == 'CA.CA')    $part->pricing['compareToJobberListDec'] = $part->pricingRow['BKMP_HEAD_JOBBR'] * $part->exchangeRate;
            if($part->pricing['singlePriceDec'] >$part->pricing['compareToJobberListDec']) { $part->pricing['singleListDec'] = $part->pricing['singlePriceDec']; }
            else                                          { $part->pricing['singleListDec'] = $part->pricing['compareToJobberListDec']; }
            if($this->debug)   echo '<p><b>jobber list dec to compare to '.$part->pricing['compareToJobberListDec'].'</b></p>';
        }//end if
        */
        /* 
        if(($part->pricingLevelRule['BKPRULES_LIST'] == '' ||     
            $part->pricingLevelRule['BKPRULES_LIST'] == 'JOBBR') && 
            isset($part->pricingRow['BKMP_HEAD_JOBBR']))
                $part->pricing['singleListDec'] = $part->pricingRow['BKMP_HEAD_JOBBR'];                                                                           //if D1-D5 set the base list price as the calculated single piece price
        */
        
        /*
        if(floatval($part->pricingLevelRule['BKPRULES_LISTF']) > 0) $part->pricing['singleListDec'] *= floatval($part->pricingLevelRule['BKPRULES_LISTF']); //mulitply the list price by the list factor (Note: for bosy shops this value is set to zero in the bkprules table. 6/26/08)
        if($this->systemID == 'CA.CA' && $part->pricingLevelRule['BKPRULES_SINGLE'] != 'BLIST') $part->pricing['singleListDec'] *= $part->exchangeRate;                     //BSLIST has already been converted  //multiply by the exhange price if this is a ca.ca
        */
        
        //removed 2021-04-19
        //if(!$this->is800 && $part->pricingLevelRule['BKPRULES_RNDSNP'] == 1 && 
        
        if($part->pricingLevelRule['BKPRULES_RNDSNP'] == 1 && 
            floatval($part->pricing['singleListDec']) >= $part->pricingLevelRule['BKPRULES_RNDBEL'])
                $part->pricing['singlePriceDec'] = $this->roundWithRuleOfFive($part->pricing['singlePriceDec']);                                                                     //round the cost for the J1 and GP pricing level

        /*
        if($part->pricingLevelRule['BKPRULES_RNDLP'] == 1 && 
            $part->pricing['singleListDec'] > 0 && 
            floatval($part->pricing['singleListDec']) >= $part->pricingLevelRule['BKPRULES_RNDBEL'])
                $part->pricing['singleListDec'] = $this->roundWithRuleOfFive($part->pricing['singleListDec']);                                                                //round the list for the J1, GP, and D1-D5 pricing levels
        */
        /*
        $part->pricing['singlePriceDec'] = $part->pricing['singlePriceDec'];                                                                //set the prices to our return array
        $part->pricing['singleListDec']  = $part->pricing['singleListDec'];
        */
        //if($this->debug)               echo '<p>Actual price: '.$part->pricing['singlePriceDec'].'</p>';

        if($this->friendlyDistBool && $part->distPricingLevel) {                                                                             //check to see if we need to set the friendly distributor jobber price
            $part->pricing['fdJobberPriceDec'] = $part->pricingRow['BKMP_HEAD_JOBBR'];

            if($this->systemID == 'CA.CA')
                $part->pricing['fdJobberPriceDec'] = (($part->pricing['fdJobberPriceDec'] * 
                                                    $part->exchangeRate* 
                                                    $part->pricingLevelRule['BKPRULES_CANFAC']) + 
                                                    $part->pricingLevelRule['BKPRULES_CANSUR']);

            if($this->systemID == 'US.CA')
                $part->pricing['fdJobberPriceDec'] = (($part->pricing['fdJobberPriceDec'] * 
                                                    $part->exchangeRate* 
                                                    $part->pricingLevelRule['BKPRULES_CANFAC']) + 
                                                    $part->pricingLevelRule['BKPRULES_CANSUR']) / $part->exchangeRate;

        }
        
        return $part;
    }//end single2
      
}

/*
if(isset($_GET['cc']) && isset($_GET['part'])){
    
 $p=new pricing($_GET['cc'],true);
 $p->getPricesForPart($_GET['part']);
 $p->showPartData();   
} */

?>
