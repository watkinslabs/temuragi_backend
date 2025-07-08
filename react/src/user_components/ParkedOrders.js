/**
 * @routes ["ParkedOrders"]
*/

import React from 'react';

const ParkedOrders = () => {
    // Use the global ServerDataTable directly
    const ServerDataTable = window.Components?.ServerDataTable;
    
    if (!ServerDataTable) {
        console.error('ServerDataTable not found in window.Components:', window.Components);
        return <div>Error: ServerDataTable component not found</div>;
    }
    
    return (
        <ServerDataTable 
            report_id="fb2d204e-5943-43b2-a20b-fe19fb1d1853"
        />
    );
};

export default ParkedOrders;