const API_BASE_URL = "http://127.0.0.1:8000";


// ---------------------------------------------------------
// Load dashboard summary
// ---------------------------------------------------------

async function loadDashboardSummary() {

    try {

        console.log("Loading dashboard data...");

        const response = await fetch(
            `${API_BASE_URL}/api/dashboard/summary`
        );

        if (!response.ok) {

            throw new Error(
                `API request failed: ${response.status}`
            );
        }

        const result = await response.json();

        console.log(
            "Dashboard data received:",
            result
        );

        if (!result.success) {

            throw new Error(
                "Dashboard API returned an unsuccessful response."
            );
        }

        const data = result.data;

        const customerElement =
            document.getElementById("customerCount");

        if (customerElement) {
            customerElement.textContent = data.total_customers;
        }

        const orderElement =
            document.getElementById("orderCount");

        if (orderElement) {
            orderElement.textContent = data.total_orders;
        }

        const productElement =
            document.getElementById("productCount");

        if (productElement) {
            productElement.textContent = data.total_products;
        }

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

        console.log("Dashboard KPIs updated successfully.");

    }

    catch (error) {

        console.error(
            "Failed to load dashboard:",
            error
        );
    }
}


// ---------------------------------------------------------
// Load revenue over time chart
// ---------------------------------------------------------

async function loadRevenueOverTime() {
    const chartContainer = document.getElementById("revenueChart");
    const labelsContainer = document.getElementById("revenueChartLabels");

    if (!chartContainer || !labelsContainer) {
        return;
    }

    try {
        console.log("Loading revenue over time...");
        const response = await fetch(
            `${API_BASE_URL}/api/dashboard/revenue-over-time`
        );

        if (!response.ok) {
            throw new Error(
                `API request failed: ${response.status}`
            );
        }

        const result = await response.json();

        if (!result.success || !result.data.length) {
            chartContainer.innerHTML =
                "<p>No revenue data available.</p>";
            return;
        }

        const points = result.data;

        const maxRevenue = Math.max(
            ...points.map(point => point.total_revenue)
        );

        chartContainer.innerHTML = "";
        labelsContainer.innerHTML = "";

        points.forEach(point => {

            const heightPercent = maxRevenue > 0
                ? (point.total_revenue / maxRevenue) * 100
                : 0;

            const bar = document.createElement("span");
            bar.style.height = `${heightPercent}%`;
            bar.title = `${point.order_date}: $${point.total_revenue}`;

            chartContainer.appendChild(bar);

            const label = document.createElement("span");
            label.textContent = point.order_date.slice(5);

            labelsContainer.appendChild(label);

        });

        console.log("Revenue over time chart updated.");

    }

    catch (error) {
        console.error(
            "Failed to load revenue over time:",
            error
        );

        chartContainer.innerHTML =
            "<p>Unable to load revenue data.</p>";
    }
}


// ---------------------------------------------------------
// Load revenue by product chart
// ---------------------------------------------------------

async function loadRevenueByProduct() {
    const chartContainer = document.getElementById("productChart");
    if (!chartContainer) {
        return;
    }
    try {
        console.log("Loading revenue by product...");
        const response = await fetch(
            `${API_BASE_URL}/api/dashboard/revenue-by-product`
        );
        if (!response.ok) {
            throw new Error(
                `API request failed: ${response.status}`
            );
        }
        const result = await response.json();
        if (!result.success || !result.data.length) {
            chartContainer.innerHTML =
                "<p>No product data available.</p>";
            return;
        }

        const products = result.data;
        const maxRevenue = Math.max(
            ...products.map(product => product.total_revenue)
        );
        chartContainer.innerHTML = "";
        products.forEach(product => {
            const widthPercent = maxRevenue > 0
                ? (product.total_revenue / maxRevenue) * 100
                : 0;

            const item = document.createElement("div");
            item.className = "bar-item";

            const label = document.createElement("span");
            label.textContent = product.product_name;

            const bar = document.createElement("div");
            bar.className = "bar";

            const fill = document.createElement("div");
            fill.style.width = `${widthPercent}%`;
            fill.title = `$${product.total_revenue}`;

            bar.appendChild(fill);
            item.appendChild(label);
            item.appendChild(bar);

            chartContainer.appendChild(item);

        });

        console.log("Revenue by product chart updated.");

    }

    catch (error) {

        console.error(
            "Failed to load revenue by product:",
            error
        );

        chartContainer.innerHTML =
            "<p>Unable to load product data.</p>";
    }
}


async function loadRevenueByCustomer() {
    const chartContainer = document.getElementById("customerChart");
    if (!chartContainer) {
        return;
    }   

    try{
        console.log("Loading revenue by customer...");
        const response = await fetch(
            `${API_BASE_URL}/api/dashboard/revenue-by-customer`
        );

        if (!response.ok) {
            throw new Error(
                `API request failed: ${response.status}`
            );
        }  
        const result = await response.json();

        if (!result.success || !result.data.length) {
            chartContainer.innerHTML =
                "<p>No customer data available.</p>";
            return;
        }
        const customers = result.data;
        const maxRevenue = Math.max(
            ...customers.map(customer => customer.total_revenue)
        );
        chartContainer.innerHTML = "";
        
        customers.forEach(customer => {
            const widthPercent = maxRevenue > 0
                ? (customer.total_revenue / maxRevenue) * 100 : 0;
            
        const item = document.createElement("div");
        item.className = "bar-item";

        const label = document.createElement("span");
        label.textContent = customer.customer_name; 

        const bar = document.createElement("div");  
        bar.className = "bar";

        const fill = document.createElement("div");
        fill.style.width = `${widthPercent}%`;
        fill.title = `$${Number(customer.total_revenue).toLocaleString(
            "en-US", 
            {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            }
        )}`;

        bar.appendChild(fill);
        item.appendChild(label);
        item.appendChild(bar);

        chartContainer.appendChild(item);
        });

        console.log("Revenue by customer chart updated.");
    }
    catch(error) {
        console.error("Failed to load revenue by customer:", error);
        chartContainer.innerHTML ="<p>Unable to load customer data.</p>";
    }
}

// ---------------------------------------------------------
// Run when frontend page loads
// ---------------------------------------------------------

document.addEventListener("DOMContentLoaded", () => {

    loadDashboardSummary();
    loadRevenueOverTime();
    loadRevenueByProduct();
    loadRevenueByCustomer();

});