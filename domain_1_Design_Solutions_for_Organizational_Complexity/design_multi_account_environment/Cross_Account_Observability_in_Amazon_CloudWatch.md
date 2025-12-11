# Cross-Account Observability in Amazon CloudWatch

Cross-account observability in AWS is a key component of designing resilient and secure architectures, focusing on centralizing monitoring data (logs, metrics, and events) from numerous member accounts into a unified view for analysis.

In a multi-account environment, the foundational approach for achieving cross-account visibility relies on a central location for monitoring and governance, aligning with the structure defined by the AWS Security Reference Architecture (AWS SRA).

For comprehensive details on multi-account environment design, account structure, and governance, see [AWS Multi-Account Environment Design](./AWS_Multi_Account_Environment_Design.md).

## I. Centralization of Monitoring Data

The primary objective is to manage operational data and security findings from a central point to simplify auditing, reporting, and incident response.

• **Central Management Location**: Centralized security event notifications and auditing are managed from the dedicated Security Tooling account.

• **Specific CloudWatch Tooling**: Architectural guidance for advanced workloads, such as Generative AI, specifies the use of Amazon CloudWatch Observability Access Manager to centralize monitoring access, typically configured within the Security OU Security Tooling account.

• **Data Flow**: CloudWatch continuously collects various types of monitoring and operational data, including logs, metrics, and events. For specialized visibility, such as monitoring EC2 instance memory usage, the Unified CloudWatch Agent must be installed and configured on the source instance to push custom metrics to CloudWatch.

• **Log Processing**: Centralized metrics and log data enable the security team to configure alerts that notify administrators when system events or suspicious activity are detected.

## II. Integration and Visualization

Once data is centralized, other services are leveraged for advanced analysis and visualization across the aggregated data set:

• **Dashboards and Analysis**: Centralized monitoring data can be accessed and analyzed from the Security Tooling account. For comprehensive visualization of metrics and logs, Amazon Managed Grafana integrates with various AWS data sources, including Amazon CloudWatch.

• **Auditing and Configuration**: AWS Config often complements CloudWatch by aggregating resource configuration and compliance data from all member accounts into the centralized Security Tooling account. AWS CloudTrail organization trails also provide central auditing by logging all API activity across the entire AWS organization, routing those logs to the specialized Log Archive account.
