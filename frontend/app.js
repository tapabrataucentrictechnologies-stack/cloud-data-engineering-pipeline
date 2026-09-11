const API_BASE_URL = "http://127.0.0.1:8000";


// ---------------------------------------------------------
// Load dashboard summary
// ---------------------------------------------------------

async function loadDashboardSummary() {

    try {

        console.log("Loading dashboard data...");


        // -------------------------------------------------
        // Call FastAPI backend
        // -------------------------------------------------

        const response = await fetch(
            `${API_BASE_URL}/api/dashboard/summary`
        );


        // -------------------------------------------------
        // Check HTTP response
        // -------------------------------------------------

        if (!response.ok) {

            throw new Error(
                `API request failed: ${response.status}`
            );
        }


        // -------------------------------------------------
        // Convert response to JSON
        // -------------------------------------------------

        const result = await response.json();

        console.log(
            "Dashboard data received:",
            result
        );


        // -------------------------------------------------
        // Check API response
        // -------------------------------------------------

        if (!result.success) {

            throw new Error(
                "Dashboard API returned an unsuccessful response."
            );
        }


        const data = result.data;


        // -------------------------------------------------
        // Update Customers KPI
        // -------------------------------------------------

        const customerElement =
            document.getElementById("customerCount");

        if (customerElement) {

            customerElement.textContent =
                data.total_customers;
        }


        // -------------------------------------------------
        // Update Orders KPI
        // -------------------------------------------------

        const orderElement =
            document.getElementById("orderCount");

        if (orderElement) {

            orderElement.textContent =
                data.total_orders;
        }


        // -------------------------------------------------
        // Update Products KPI
        // -------------------------------------------------

        const productElement =
            document.getElementById("productCount");

        if (productElement) {

            productElement.textContent =
                data.total_products;
        }


        // -------------------------------------------------
        // Update Revenue KPI
        // -------------------------------------------------

        const revenueElement =
            document.getElementById("revenueValue");

        if (revenueElement) {

            revenueElement.textContent =
                Number(data.total_revenue).toLocaleString(
                    "en-US",
                    {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2
                    }
                );
        }


        console.log(
            "Dashboard KPIs updated successfully."
        );

    }


    catch (error) {

        console.error(
            "Failed to load dashboard:",
            error
        );
    }
}


// ---------------------------------------------------------
// Run when frontend page loads
// ---------------------------------------------------------

document.addEventListener(
    "DOMContentLoaded",
    loadDashboardSummary
);