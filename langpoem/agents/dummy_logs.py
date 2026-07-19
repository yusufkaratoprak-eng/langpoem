# Manually maintained stand-in for Application Insights exception telemetry,
# used when APPINSIGHT_LOCAL is enabled. Field names follow the real
# `exceptions` table schema (operation_Id / operation_ParentId are the
# standard AppInsights correlation IDs used for lookups). trackId isn't a
# real AppInsights column, so it lives in customDimensions like any other
# app-defined custom property.
DUMMY_LOGS = [
    {
        "timestamp": "2026-07-10T08:15:32Z",
        "operation_Id": "6a3fd8b2-9e21-4c3a-8f0d-1a2b3c4d5e6f",
        "operation_ParentId": "1f2e3d4c-5b6a-4798-8c9d-0a1b2c3d4e5f",
        "operation_Name": "POST /api/orders",
        "problemId": "NullReferenceException at OrderService.Process",
        "severityLevel": 3,
        "outerMessage": "Object reference not set to an instance of an object.",
        "customDimensions": {"trackId": "TRK-1001"},
    },
    {
        "timestamp": "2026-07-11T14:02:10Z",
        "operation_Id": "b7e4c1a0-3f5d-4e2b-9a6c-7d8e9f0a1b2c",
        "operation_ParentId": "2c3d4e5f-6a7b-48c9-9d0e-1f2a3b4c5d6e",
        "operation_Name": "POST /api/payments",
        "problemId": "SqlTimeoutException at PaymentRepository.Save",
        "severityLevel": 4,
        "outerMessage": "Timeout expired while waiting for the SQL connection pool.",
        "customDimensions": {"trackId": "TRK-1002"},
    },
    {
        "timestamp": "2026-07-12T09:47:55Z",
        "operation_Id": "f1a2b3c4-d5e6-4f7a-8b9c-0d1e2f3a4b5c",
        "operation_ParentId": "3d4e5f6a-7b8c-49d0-8e1f-2a3b4c5d6e7f",
        "operation_Name": "GET /api/inventory",
        "problemId": "HttpRequestException at InventoryClient.GetStock",
        "severityLevel": 2,
        "outerMessage": "Connection refused by the downstream inventory service.",
        "customDimensions": {"trackId": "TRK-1003"},
    },
]
