import pandas as pd
import yaml
import os
import ipaddress
import logging
from tqdm import tqdm

# Set up logging to track the script's actions and errors
logging.basicConfig(
    filename='customer_processing.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Convert subnet mask to CIDR notation (e.g., 255.255.255.0 -> 24)
def subnet_mask_to_cidr(subnet_mask):
    return ipaddress.IPv4Network(f"0.0.0.0/{subnet_mask}").prefixlen

# Generate an object name in the format CustomerName_IPAddress_CIDR
def generate_object_name(name, ip_address, subnet_mask):
    cidr = subnet_mask_to_cidr(subnet_mask)
    return f"{name}_{ip_address}_{cidr}"

# Validate and process customer data to ensure accuracy and uniqueness
def validate_customer_data(customers):
    validated_customers = []
    object_names = set()  # Track object names to avoid duplicates

    logging.info("Starting customer data validation...")
    print("\nValidating customer data...")

    for customer in tqdm(customers, desc="Validating", unit="customer"):
        try:
            # Extract and clean input fields
            name = customer.get('CustomerName', '').strip()
            ip_address = customer.get('CustomerIPAddress', '').strip()
            subnet_mask = customer.get('IPSubnetMask', '').strip()
            tags = customer.get('Tags', '')

            # Generate the object name for the firewall entry
            object_name = generate_object_name(name, ip_address, subnet_mask)

            # Check for duplicate object names
            if object_name in object_names:
                logging.warning(f"Duplicate object name '{object_name}' detected. Skipping.")
                continue
            object_names.add(object_name)

            # Process and split tags into a list
            customer['ObjectName'] = object_name
            customer['Tags'] = [tag.strip() for tag in tags.split(',') if tag.strip()]

            # Add validated customer to the list
            validated_customers.append(customer)

        except Exception as e:
            logging.error(f"Validation error: {e}")
            continue

    logging.info("Customer data validation completed.")
    return validated_customers

# Main function to handle file input and output
def main():
    # Prompt the user for the file path
    file_path = input("Enter the path to the Excel or CSV file: ").strip()

    # Load the file based on its extension
    df = pd.read_csv(file_path) if file_path.endswith('.csv') else pd.read_excel(file_path)
    customers = df.to_dict(orient='records')

    # Validate the customer data
    validated_customers = validate_customer_data(customers)

    # Save the validated data to a YAML file
    with open('customers.yml', 'w') as file:
        yaml.dump({'customers': validated_customers}, file)

    print("Customer data successfully saved to customers.yml.")

# Entry point of the script
if __name__ == "__main__":
    main()
