const API_BASE_URL = "http://127.0.0.1:8000";

let selectedFile = null;


// =========================================================
// PIPELINE STATUS
// =========================================================

function updatePipelineStatus(status, selectedFileName = null) {

    const statusDot =
        document.getElementById("statusDot");

    const statusText =
        document.getElementById("pipelineStatusText");

    const statusSubtext =
        document.getElementById("pipelineStatusSubtext");

    if (!statusDot || !statusText || !statusSubtext) {
        return;
    }

    statusDot.className = "status-dot";

    if (status === "idle") {

        statusText.textContent =
            "Ready for execution";

        statusSubtext.textContent =
            selectedFileName
                ? `Selected: ${selectedFileName}`
                : "Select a dataset to begin";
    }

    else if (status === "running") {

        statusDot.classList.add(
            "status-running"
        );

        statusText.textContent =
            "Pipeline Running";

        statusSubtext.textContent =
            selectedFileName
                ? `Processing ${selectedFileName}`
                : "Processing dataset...";
    }

    else if (status === "completed") {

        statusDot.classList.add(
            "status-completed"
        );

        statusText.textContent =
            "Pipeline Completed";

        statusSubtext.textContent =
            selectedFileName
                ? `${selectedFileName} processed successfully`
                : "Pipeline completed successfully";
    }

    else if (status === "failed") {

        statusDot.classList.add(
            "status-error"
        );

        statusText.textContent =
            "Pipeline Failed";

        statusSubtext.textContent =
            "Check the pipeline message";
    }
}


// =========================================================
// LOAD FILES FROM GOOGLE DRIVE
// =========================================================

async function loadAvailableFiles() {

    const loadingElement =
        document.getElementById("filesLoading");

    const fileList =
        document.getElementById("fileList");

    const runButton =
        document.getElementById("runPipelineBtn");

    if (!fileList) {
        return;
    }

    try {

        if (loadingElement) {

            loadingElement.style.display =
                "block";

            loadingElement.className =
                "pipeline-message";

            loadingElement.textContent =
                "Loading files from Google Drive...";
        }

        fileList.innerHTML = "";

        selectedFile = null;

        if (runButton) {
            runButton.disabled = true;
        }

        updatePipelineStatus("idle");


        // -------------------------------------------------
        // IMPORTANT:
        // FastAPI route is /api/pipeline/files
        // -------------------------------------------------

        const response = await fetch(
            `${API_BASE_URL}/api/pipeline/files`
        );


        if (!response.ok) {

            throw new Error(
                `API request failed: ${response.status}`
            );
        }


        const result =
            await response.json();

        console.log(
            "Google Drive files received:",
            result
        );


        if (!result.success) {

            throw new Error(
                "Unable to load files from Google Drive."
            );
        }


        // -------------------------------------------------
        // pipeline.py returns:
        //
        // {
        //   success: true,
        //   count: ...,
        //   files: [...]
        // }
        // -------------------------------------------------

        const files =
            result.files || [];


        if (files.length === 0) {

            if (loadingElement) {

                loadingElement.className =
                    "pipeline-message";

                loadingElement.textContent =
                    "No supported files found in Google Drive.";
            }

            return;
        }


        if (loadingElement) {
            loadingElement.style.display =
                "none";
        }


        // -------------------------------------------------
        // Create file options
        // -------------------------------------------------

        files.forEach(file => {

            const option =
                document.createElement("div");

            option.className =
                "file-option";


            // File icon

            const icon =
                document.createElement("div");

            icon.className =
                "file-icon";

            icon.textContent =
                getFileIcon(file.extension);


            // File information

            const information =
                document.createElement("div");

            information.className =
                "file-information";


            const name =
                document.createElement("strong");

            name.textContent =
                file.name;


            const details =
                document.createElement("small");

            details.textContent =
                `${file.type} file`;


            information.appendChild(name);
            information.appendChild(details);


            // Radio button

            const radio =
                document.createElement("input");

            radio.type =
                "radio";

            radio.name =
                "dataset";

            radio.value =
                file.name;


            // ------------------------------------------------
            // Select file
            // ------------------------------------------------

            radio.addEventListener(
                "change",
                () => {

                    document
                        .querySelectorAll(".file-option")
                        .forEach(item => {

                            item.classList.remove(
                                "selected"
                            );

                        });


                    option.classList.add(
                        "selected"
                    );


                    selectedFile =
                        file.name;


                    updateSelectedFile(
                        file.name
                    );


                    if (runButton) {

                        runButton.disabled =
                            false;

                    }


                    updatePipelineStatus(
                        "idle",
                        file.name
                    );

                }
            );


            option.appendChild(icon);
            option.appendChild(information);
            option.appendChild(radio);


            // Allow clicking anywhere on the row

            option.addEventListener(
                "click",
                event => {

                    if (
                        event.target !== radio
                    ) {

                        radio.checked =
                            true;

                        radio.dispatchEvent(
                            new Event("change")
                        );

                    }

                }
            );


            fileList.appendChild(
                option
            );

        });


        console.log(
            `${files.length} files loaded successfully.`
        );

    }

    catch (error) {

        console.error(
            "Failed to load Google Drive files:",
            error
        );


        if (loadingElement) {

            loadingElement.style.display =
                "block";

            loadingElement.className =
                "pipeline-message error";

            loadingElement.textContent =
                "Unable to load files from Google Drive.";
        }


        fileList.innerHTML = "";

        if (runButton) {
            runButton.disabled = true;
        }

    }
}


// =========================================================
// FILE ICON
// =========================================================

function getFileIcon(extension) {

    switch (extension) {

        case ".csv":
            return "▤";

        case ".json":
            return "{}";

        case ".xml":
            return "</>";

        case ".xlsx":
            return "▦";

        default:
            return "📄";
    }
}


// =========================================================
// UPDATE SELECTED FILE
// =========================================================

function updateSelectedFile(fileName) {

    const selectedInfo =
        document.getElementById(
            "selectedFileInfo"
        );

    const selectedName =
        document.getElementById(
            "selectedFileName"
        );


    if (selectedInfo) {

        selectedInfo.style.display =
            "block";
    }


    if (selectedName) {

        selectedName.textContent =
            fileName;
    }
}


// =========================================================
// RUN PIPELINE
// =========================================================

async function runSelectedPipeline() {

    const runButton =
        document.getElementById(
            "runPipelineBtn"
        );

    const message =
        document.getElementById(
            "pipelineMessage"
        );


    if (!selectedFile) {

        return;
    }


    try {

        // -------------------------------------------------
        // Disable button
        // -------------------------------------------------

        if (runButton) {

            runButton.disabled =
                true;

            runButton.textContent =
                "⏳ Running Pipeline...";
        }


        // -------------------------------------------------
        // Show running message
        // -------------------------------------------------

        if (message) {

            message.style.display =
                "block";

            message.className =
                "pipeline-message running";

            message.textContent =
                `Running pipeline for ${selectedFile}...`;
        }


        updatePipelineStatus(
            "running",
            selectedFile
        );


        // -------------------------------------------------
        // Update pipeline stages
        // -------------------------------------------------

        resetPipelineStages();

        setStageRunning(
            "stageRaw"
        );


        // -------------------------------------------------
        // Call FastAPI
        // -------------------------------------------------

        const response =
            await fetch(
                `${API_BASE_URL}/api/pipeline/run`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json",

                        "Accept":
                            "application/json"
                    },

                    body: JSON.stringify({
                        selected_file:
                            selectedFile
                    })
                }
            );


        const result =
            await response.json();


        console.log(
            "Pipeline result:",
            result
        );


        if (!response.ok ||
            !result.success) {

            throw new Error(
                result.detail ||
                result.message ||
                "Pipeline execution failed."
            );
        }


        // -------------------------------------------------
        // Pipeline successful
        // -------------------------------------------------

        setStageCompleted(
            "stageRaw"
        );

        setStageCompleted(
            "stageSpark"
        );

        setStageCompleted(
            "stageValidation"
        );

        setStageCompleted(
            "stageBigQuery"
        );

        setStageCompleted(
            "stageAnalytics"
        );


        updatePipelineStatus(
            "completed",
            selectedFile
        );


        // -------------------------------------------------
        // Show success message
        // -------------------------------------------------

        if (message) {

            message.style.display =
                "block";

            message.className =
                "pipeline-message success";

            message.textContent =
                "Pipeline completed successfully.";
        }


        // -------------------------------------------------
        // Display result
        // -------------------------------------------------

        displayPipelineResult(
            result.data
        );


        // -------------------------------------------------
        // Refresh dashboard
        // -------------------------------------------------

        await loadDashboardSummary();

        await loadRevenueOverTime();

        await loadRevenueByProduct();

        await loadRevenueByCustomer();


        console.log(
            "Dashboard refreshed after pipeline execution."
        );

    }

    catch (error) {

        console.error(
            "Pipeline execution failed:",
            error
        );


        updatePipelineStatus(
            "failed",
            selectedFile
        );


        markPipelineFailed();


        if (message) {

            message.style.display =
                "block";

            message.className =
                "pipeline-message error";

            message.textContent =
                `Pipeline failed: ${error.message}`;
        }

    }

    finally {

        if (runButton) {

            runButton.disabled =
                !selectedFile;

            runButton.textContent =
                "▶ Run Pipeline";
        }

    }
}


// =========================================================
// DISPLAY PIPELINE RESULT
// =========================================================

function displayPipelineResult(data) {

    if (!data) {
        return;
    }


    const resultSection =
        document.getElementById(
            "resultSection"
        );


    if (resultSection) {

        resultSection.style.display =
            "block";
    }


    const sourceFile =
        document.getElementById(
            "resultSourceFile"
        );

    const processedFile =
        document.getElementById(
            "resultProcessedFile"
        );

    const bigqueryTable =
        document.getElementById(
            "resultBigQueryTable"
        );

    const rowsLoaded =
        document.getElementById(
            "resultRowsLoaded"
        );


    if (sourceFile) {

        sourceFile.textContent =
            data.source_file || "-";
    }


    if (processedFile) {

        processedFile.textContent =
            data.processed_file || "-";
    }


    if (bigqueryTable) {

        bigqueryTable.textContent =
            data.bigquery_table || "-";
    }


    if (rowsLoaded) {

        rowsLoaded.textContent =
            data.rows_loaded ?? "-";
    }
}


// =========================================================
// PIPELINE STAGES
// =========================================================

function resetPipelineStages() {

    const stages = [
        "stageRaw",
        "stageSpark",
        "stageValidation",
        "stageBigQuery",
        "stageAnalytics"
    ];


    stages.forEach(id => {

        const stage =
            document.getElementById(id);

        if (!stage) {
            return;
        }

        stage.classList.remove(
            "completed",
            "running",
            "failed"
        );

    });


    // Raw data is available immediately

    const raw =
        document.getElementById(
            "stageRaw"
        );

    if (raw) {

        raw.classList.add(
            "completed"
        );
    }
}


function setStageRunning(stageId) {

    const stage =
        document.getElementById(
            stageId
        );

    if (!stage) {
        return;
    }


    stage.classList.add(
        "running"
    );
}


function setStageCompleted(stageId) {

    const stage =
        document.getElementById(
            stageId
        );

    if (!stage) {
        return;
    }


    stage.classList.remove(
        "running",
        "failed"
    );

    stage.classList.add(
        "completed"
    );
}


function markPipelineFailed() {

    const stages = [
        "stageSpark",
        "stageValidation",
        "stageBigQuery",
        "stageAnalytics"
    ];


    stages.forEach(id => {

        const stage =
            document.getElementById(id);

        if (
            stage &&
            !stage.classList.contains(
                "completed"
            )
        ) {

            stage.classList.add(
                "failed"
            );

            return;
        }

    });
}


// =========================================================
// LOAD DASHBOARD SUMMARY
// =========================================================

async function loadDashboardSummary() {

    try {

        console.log(
            "Loading dashboard data..."
        );


        const response =
            await fetch(
                `${API_BASE_URL}/api/dashboard/summary`
            );


        if (!response.ok) {

            throw new Error(
                `API request failed: ${response.status}`
            );
        }


        const result =
            await response.json();


        if (!result.success) {

            throw new Error(
                "Dashboard API returned an unsuccessful response."
            );
        }


        const data =
            result.data;


        const customerElement =
            document.getElementById(
                "customerCount"
            );


        if (customerElement) {

            customerElement.textContent =
                data.total_customers;
        }


        const orderElement =
            document.getElementById(
                "orderCount"
            );


        if (orderElement) {

            orderElement.textContent =
                data.total_orders;
        }


        const productElement =
            document.getElementById(
                "productCount"
            );


        if (productElement) {

            productElement.textContent =
                data.total_products;
        }


        const revenueElement =
            document.getElementById(
                "revenueValue"
            );


        if (revenueElement) {

            revenueElement.textContent =
                Number(
                    data.total_revenue
                ).toLocaleString(
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


// =========================================================
// REVENUE OVER TIME
// =========================================================

async function loadRevenueOverTime() {

    const chartContainer =
        document.getElementById(
            "revenueChart"
        );

    const labelsContainer =
        document.getElementById(
            "revenueChartLabels"
        );


    if (
        !chartContainer ||
        !labelsContainer
    ) {
        return;
    }


    try {

        const response =
            await fetch(
                `${API_BASE_URL}/api/dashboard/revenue-over-time`
            );


        if (!response.ok) {

            throw new Error(
                `API request failed: ${response.status}`
            );
        }


        const result =
            await response.json();


        if (
            !result.success ||
            !result.data.length
        ) {

            chartContainer.innerHTML =
                "<p>No revenue data available.</p>";

            return;
        }


        const points =
            result.data;


        const maxRevenue =
            Math.max(
                ...points.map(
                    point =>
                        point.total_revenue
                )
            );


        chartContainer.innerHTML =
            "";

        labelsContainer.innerHTML =
            "";


        points.forEach(point => {

            const heightPercent =
                maxRevenue > 0
                    ? (
                        point.total_revenue /
                        maxRevenue
                    ) * 100
                    : 0;


            const bar =
                document.createElement(
                    "span"
                );


            bar.style.height =
                `${heightPercent}%`;


            bar.title =
                `${point.order_date}: ${point.total_revenue}`;


            chartContainer.appendChild(
                bar
            );


            const label =
                document.createElement(
                    "span"
                );


            label.textContent =
                point.order_date.slice(
                    5
                );


            labelsContainer.appendChild(
                label
            );

        });

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


// =========================================================
// REVENUE BY PRODUCT
// =========================================================

async function loadRevenueByProduct() {

    const chartContainer =
        document.getElementById(
            "productChart"
        );


    if (!chartContainer) {
        return;
    }


    try {

        const response =
            await fetch(
                `${API_BASE_URL}/api/dashboard/revenue-by-product`
            );


        if (!response.ok) {

            throw new Error(
                `API request failed: ${response.status}`
            );
        }


        const result =
            await response.json();


        if (
            !result.success ||
            !result.data.length
        ) {

            chartContainer.innerHTML =
                "<p>No product data available.</p>";

            return;
        }


        const products =
            result.data;


        const maxRevenue =
            Math.max(
                ...products.map(
                    product =>
                        product.total_revenue
                )
            );


        chartContainer.innerHTML =
            "";


        products.forEach(product => {

            const widthPercent =
                maxRevenue > 0
                    ? (
                        product.total_revenue /
                        maxRevenue
                    ) * 100
                    : 0;


            const item =
                document.createElement(
                    "div"
                );

            item.className =
                "bar-item";


            const label =
                document.createElement(
                    "span"
                );

            label.textContent =
                product.product_name;


            const bar =
                document.createElement(
                    "div"
                );

            bar.className =
                "bar";


            const fill =
                document.createElement(
                    "div"
                );


            fill.style.width =
                `${widthPercent}%`;


            fill.title =
                `${product.total_revenue}`;


            bar.appendChild(
                fill
            );


            item.appendChild(
                label
            );

            item.appendChild(
                bar
            );


            chartContainer.appendChild(
                item
            );

        });

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


// =========================================================
// REVENUE BY CUSTOMER
// =========================================================

async function loadRevenueByCustomer() {

    const chartContainer =
        document.getElementById(
            "customerChart"
        );


    if (!chartContainer) {
        return;
    }


    try {

        const response =
            await fetch(
                `${API_BASE_URL}/api/dashboard/revenue-by-customer`
            );


        if (!response.ok) {

            throw new Error(
                `API request failed: ${response.status}`
            );
        }


        const result =
            await response.json();


        if (
            !result.success ||
            !result.data.length
        ) {

            chartContainer.innerHTML =
                "<p>No customer data available.</p>";

            return;
        }


        const customers =
            result.data;


        const maxRevenue =
            Math.max(
                ...customers.map(
                    customer =>
                        customer.total_revenue
                )
            );


        chartContainer.innerHTML =
            "";


        customers.forEach(customer => {

            const widthPercent =
                maxRevenue > 0
                    ? (
                        customer.total_revenue /
                        maxRevenue
                    ) * 100
                    : 0;


            const item =
                document.createElement(
                    "div"
                );

            item.className =
                "bar-item";


            const label =
                document.createElement(
                    "span"
                );

            label.textContent =
                customer.customer_name;


            const bar =
                document.createElement(
                    "div"
                );

            bar.className =
                "bar";


            const fill =
                document.createElement(
                    "div"
                );


            fill.style.width =
                `${widthPercent}%`;


            fill.title =
                Number(
                    customer.total_revenue
                ).toLocaleString(
                    "en-US",
                    {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2
                    }
                );


            bar.appendChild(
                fill
            );


            item.appendChild(
                label
            );

            item.appendChild(
                bar
            );


            chartContainer.appendChild(
                item
            );

        });

    }

    catch (error) {

        console.error(
            "Failed to load revenue by customer:",
            error
        );


        chartContainer.innerHTML =
            "<p>Unable to load customer data.</p>";
    }
}


// =========================================================
// REFRESH FILES BUTTON
// =========================================================

function setupRefreshButton() {

    const button =
        document.getElementById(
            "refreshFilesBtn"
        );


    if (!button) {
        return;
    }


    button.addEventListener(
        "click",
        () => {

            loadAvailableFiles();

        }
    );
}


// =========================================================
// RUN PIPELINE BUTTON
// =========================================================

function setupRunPipelineButton() {

    const button =
        document.getElementById(
            "runPipelineBtn"
        );


    if (!button) {
        return;
    }


    button.addEventListener(
        "click",
        () => {

            runSelectedPipeline();

        }
    );
}


// =========================================================
// INITIALIZE APPLICATION
// =========================================================

document.addEventListener(
    "DOMContentLoaded",
    () => {

        console.log(
            "Cloud Data Engineering Pipeline frontend started."
        );


        // Dynamic Drive files

        loadAvailableFiles();


        // Buttons

        setupRefreshButton();

        setupRunPipelineButton();


        // Existing dashboard

        loadDashboardSummary();

        loadRevenueOverTime();

        loadRevenueByProduct();

        loadRevenueByCustomer();

    }
);