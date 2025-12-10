# AWS PrivateLink

AWS PrivateLink is a foundational networking service that simplifies the security of data sharing with cloud-based applications by keeping data exposure off the public internet. It establishes private connectivity between Virtual Private Clouds (VPCs), AWS services, and on-premises applications, operating securely on the Amazon network. This capability is instrumental in enabling the connection of services across different accounts and VPCs while substantially simplifying network architecture.

## Architecture Design

The following diagram illustrates a typical AWS PrivateLink architecture using a VPC Gateway Endpoint for Amazon S3, demonstrating how private instances can securely access S3 buckets without traversing the public internet:

![AWS PrivateLink Architecture](../images/AWSPrivateLink.png)

**Key Architectural Components:**

- **VPC with Public and Private Subnets**: The VPC contains both public and private subnets, allowing for secure network segmentation.
- **Public Instance**: Acts as a bastion/jump server in the public subnet with internet access via an Internet Gateway.
- **Private Instance**: Resides in the private subnet without direct internet access, ensuring enhanced security.
- **VPC Gateway Endpoint for S3**: Provides a direct, private connection from the private instance to the S3 bucket, ensuring traffic remains within the AWS network and never traverses the public internet.
- **Security Groups**: Applied to both instances to control inbound and outbound traffic at the instance level.

This architecture ensures that sensitive data stored in S3, when accessed by the private instance, never leaves the Amazon network, significantly enhancing security and compliance.

## Core Configuration using VPC Endpoints

PrivateLink powers the creation of VPC interface endpoints, which serve as private connection points within your virtual network. These endpoints function as a critical layer of security control, allowing private connections to supported AWS services without requiring an internet gateway, Network Address Translation (NAT) device, or VPN connection.

Configuration involves selecting and setting up specific types of endpoints:

### 1. Interface Endpoints

These are powered by AWS PrivateLink and typically provision an Elastic Network Interface (ENI) that uses a private IP address as its entry point. Interface endpoints are generally preferred when access to AWS services is required from on-premises environments, such as over AWS Direct Connect or AWS Site-to-Site VPN.

### 2. Gateway Endpoints

These provision a gateway instead of an ENI, and are configured as targets in the VPC route table. Gateway Endpoints specifically support access to Amazon S3 and Amazon DynamoDB. To properly implement a private subnet staging area for recovery services, ensuring resources can download software, both an EC2 Interface Endpoint and an S3 Gateway Endpoint must be created.

### Networking Components

For effective deployment, the following networking components are typically required:

• **Network Components**: Deploying PrivateLink connectivity typically requires a Network Load Balancer (NLB) on the service VPC side (the service provider) and an ENI on the customer VPC side (the service consumer).

• **Endpoint Policies**: Access control is managed through a VPC endpoint policy, which is an IAM resource policy attached directly to the endpoint. This provides an additional layer of control over which AWS principals can communicate with the associated AWS service.

## Deployment Example for Secured Environments (AWS Elastic Disaster Recovery)

AWS services often use PrivateLink-powered endpoints to facilitate secure management and data movement, especially in hybrid or private network architectures. When deploying the AWS Replication Agent on a network that restricts outbound access to default AWS endpoints, specific PrivateLink endpoints must be configured:

### 1. DRS Service Endpoint

Create an interface VPC endpoint specifically for the AWS Elastic Disaster Recovery (DRS) service manager in your staging area subnet. This endpoint handles management traffic, while the bulk replication data transmits directly between source and replication servers.

### 2. S3 Software Endpoint

Create an interface S3 endpoint within the staging area subnet. This allows the Replication Agent installer to communicate with Amazon S3 to download necessary software components securely.

### 3. Agent Configuration

During agent installation, the connection must be explicitly configured using command parameters:

    ◦ The `--endpoint` installation parameter is used to specify the Private Link endpoint DNS hostname for connecting to the DRS service.

    ◦ The `--s3-endpoint` installation parameter is used to specify the corresponding Private Link DNS hostname for the S3 endpoint.

As a best practice, especially when dealing with EC2 instances, it is recommended to ensure that DNS automatically resolves the regional endpoint (e.g., `drs.{region}.amazonaws.com`) to the Private Link endpoint rather than relying solely on the `--endpoint` flag.

## How to Configure AWS PrivateLink

Configuring AWS PrivateLink involves two distinct roles: the Service Provider (who shares an application) and the Service Consumer (who connects to it). The following guide details the steps for both sides.

### Part 1: The Provider (Sharing Your Service)

**Scenario**: You have an application in your VPC and want to share it securely with another VPC or external customer without exposing it to the public internet.

#### Step 1: Prepare Your Infrastructure

PrivateLink requires a Network Load Balancer (NLB) to front your application. It does not work directly with Application Load Balancers (ALB).

1. **Create an NLB**: Go to EC2 > Load Balancers > Create Network Load Balancer.
2. **Target Group**: Point the NLB to your application instances (EC2) or IP addresses.
3. **Internal Scheme**: Ensure the NLB is "Internal" so it remains private.
4. **Cross-Zone Load Balancing**: Enable this to ensure reliability across Availability Zones (AZs).

#### Step 2: Create the Endpoint Service

1. Navigate to VPC Console > Endpoint Services > Create Endpoint Service.
2. **Load Balancer**: Select the Network Load Balancer you created in Step 1.
3. **Private DNS Name (Optional)**: If you want users to connect via a friendly name (e.g., `api.myservice.com`) instead of the AWS-generated one, enable this. Note: You will need to verify domain ownership via a TXT record.
4. **Acceptance Required**: Check this box if you want to manually approve every consumer who tries to connect (recommended for security).
5. **Create**: Click Create. Note the Service Name (e.g., `com.amazonaws.vpce.region.vpce-svc-xxxx`). You will share this string with your consumers.

#### Step 3: Whitelist Principals

By default, no one can connect.

1. Select your new Endpoint Service > Allow Principals tab.
2. Click Allow principals and enter the AWS ARN of the consumer (e.g., `arn:aws:iam::123456789012:root` for a whole account or a specific user/role ARN).

### Part 2: The Consumer (Connecting to a Service)

**Scenario**: You want to securely access an AWS Service (like S3, Systems Manager) or a Partner Service (like Snowflake, Salesforce, or the Provider above).

#### Step 1: Create the Interface Endpoint

1. Navigate to VPC Console > Endpoints > Create Endpoint.
2. **Service Category**:
   - **AWS Services**: For things like S3, EC2, Kinesis.
   - **PrivateLink Ready Partner Services**: For 3rd party SaaS.
   - **Other Endpoint Services**: If connecting to the custom provider from Part 1. (Paste the Service Name here).
3. **VPC**: Select the VPC where your client application resides.
4. **Subnets**: Select the subnets (Availability Zones) where you want the endpoint interfaces to exist. Pro tip: Select multiple AZs for high availability.
5. **Security Group**: Attach a Security Group that allows inbound HTTPS (port 443) traffic from your VPC CIDR (or the specific client instances).

#### Step 2: Enable Private DNS (Highly Recommended)

1. **Setting**: Check "Enable Private DNS Name".
2. **Why**: This allows your code to continue using the standard URL (e.g., `sqs.us-east-1.amazonaws.com`) while AWS transparently routes that traffic to the private endpoint IP instead of the public internet.
3. **Note**: If connecting to a 3rd party provider service, you might not be able to enable this until the provider verifies their domain.

#### Step 3: Wait for Acceptance

If the provider configured "Acceptance Required," your endpoint status will be Pending.

1. **Action**: Notify the provider. They must go to Endpoint Services > Endpoint Connections > Actions > Accept Request.
2. Once accepted, the status changes to Available.

### Part 3: Verification & Troubleshooting

Once the endpoint is Available, verify the connection from an EC2 instance inside the Consumer VPC.

#### 1. DNS Resolution Test

Run `nslookup` on the service domain.

```bash
nslookup service-name.region.amazonaws.com
```

- **Success**: Returns private IP addresses (e.g., `10.0.1.55`).
- **Failure**: Returns public IP addresses (e.g., `54.23.x.x`). Check "Enable Private DNS" setting.

#### 2. Connectivity Test

Use `curl` or `telnet` to test the port (usually 443).

```bash
curl -v https://service-name.region.amazonaws.com

# OR

telnet service-name.region.amazonaws.com 443
```

- **Success**: You see a "Connected" message or SSL handshake info.
- **Failure (Timeout)**: Check the Security Group attached to the Interface Endpoint. It MUST allow inbound traffic on port 443 from your client instance.

### Important: Pricing Model

Be aware that PrivateLink is not free. You are billed on two dimensions:

- **Hourly Charge**: ~$0.01 per hour per Availability Zone where an endpoint exists.
- **Data Processing**: ~$0.01 per GB of data processed.

### Summary Checklist

| Role | Key Action | Critical Config |
| :--- | :--- | :--- |
| Provider | Create NLB | Ensure NLB is Internal; Enable Cross-Zone Balancing. |
| Provider | Create Service | Whitelist Consumer ARNs; Decide on "Acceptance Required". |
| Consumer | Create Endpoint | Enable Private DNS; Ensure Security Group allows Port 443 Inbound. |
| Both | Network | Ensure VPC CIDRs do not overlap if using Peering (though PrivateLink tolerates overlap). |

## References

- [Mastering AWS Private Link (VPC Endpoint Service)](https://www.youtube.com/watch?v=example) - This video provides a practical visual walkthrough of the endpoint service setup which often clarifies the "Whitelisting" step better than text does.
- [Terraform AWS PrivateLink Example](https://github.com/shazChaudhry/terraform-aws-privateLink) - A Terraform implementation demonstrating how to provision infrastructure with VPC Gateway Endpoint for Amazon S3, including a VPC with public and private subnets, EC2 instances, and secure S3 access without internet traversal.
