import pandas as pd
from tabulate import tabulate

class TruckItemAllocator:
    # Define the class with factors namely maximum weight of each truck, weight rate, distance rate, destinations and items detail
    def __init__(self, max_weight_two_door, max_weight_one_door, weight_rate, distance_rate, destinations, items_detail):
        self.max_weight_two_door = max_weight_two_door
        self.max_weight_one_door = max_weight_one_door
        self.weight_rate = weight_rate
        self.distance_rate = distance_rate
        self.destinations = destinations
        self.items_detail = items_detail
        self.invalid_items = []
        self.process_items()

    # Volume calculation
    def calculate_volume(self, height, length, width):
        return height * length * width

    # Bill calculation (including price)
    def calculate_bill(self, weight, distance):
        return float(weight * self.weight_rate + distance * self.distance_rate)

    # Process the item the main detail to consider later on
    def process_items(self):
        valid_items = []
        for item in self.items_detail:
            if item['weight'] <= 0 or item['city'] not in self.destinations:
                self.invalid_items.append(item)
            else:
                item['volume'] = self.calculate_volume(item['height'], item['length'], item['width'])
                item['distance'] = self.destinations.get(item['city'], 0)
                item['bill'] = self.calculate_bill(item['weight'], item['distance'])
                valid_items.append(item)
        self.items_detail = valid_items

    # Knapsack recursive function
    def knapsack_method(self, weights, bills, capacity, n):
        if n == 0 or capacity == 0: # Base case
            return 0
        if weights[n - 1] > capacity: # Case of exceeding capacity, exclude the current item return default value
            return self.knapsack_method(weights, bills, capacity, n - 1)
        else: # In the case of fitting in the capacity, double into two cases check.
            return max(
                bills[n - 1] + self.knapsack_method(weights, bills, capacity - weights[n - 1], n - 1),  # Including the current item
                self.knapsack_method(weights, bills, capacity, n - 1) # Excluding that kind of item when the capacity is not able to contain anymore
            )

    # Function to find the items selected in the knapsack
    def knapsack_item_sorting(self, weights, bills, capacity, n):
        if n == 0 or capacity == 0: # Base case when no items or capacity is 0, empty list will return
            return []
        if weights[n - 1] > capacity: # Case of exceeding capacity, exclude the current item return default value
            return self.knapsack_item_sorting(weights, bills, capacity, n - 1)
        else:
            # Case of including the current item, compare the value to see which one is better of including the current item and excluding the current item
            if bills[n - 1] + self.knapsack_method(weights, bills, capacity - weights[n - 1], n - 1) >= self.knapsack_method(weights, bills, capacity, n - 1):
                return self.knapsack_item_sorting(weights, bills, capacity - weights[n - 1], n - 1) + [n - 1]
            else:
                return self.knapsack_item_sorting(weights, bills, capacity, n - 1)  # Case of excluding the current item

    # Loop function to allocate items to each truck
    def allocate_items(self):
        oversized_items = [item for item in self.items_detail if item['weight'] > self.max_weight_two_door] # Separate items that are oversized and cannot be delivered
        eligible_items = [item for item in self.items_detail if item['weight'] <= self.max_weight_two_door] # Items that can be delivered by the two-door truck as two door truck > one door truck

        eligible_weights = [item['weight'] for item in eligible_items]  # Create list of weight of the eligible items
        eligible_bills = [item['bill'] for item in eligible_items] # Create list of bill of the eligible items

        selected_one_door_indices = self.knapsack_item_sorting(eligible_weights, eligible_bills, self.max_weight_one_door, len(eligible_items)) # Find the items selected for one door truck
        one_door_truck_items = [eligible_items[i] for i in selected_one_door_indices] # Create list of items for one door truck

        remaining_indices = [i for i in range(len(eligible_items)) if i not in selected_one_door_indices] # Find not in key selection of one door truck
        remaining_items = [eligible_items[i] for i in remaining_indices] # Create list of remaining items

        remaining_weights = [item['weight'] for item in remaining_items] # Create list of weight of the remaining items
        remaining_bills = [item['bill'] for item in remaining_items] # Create list of bill of the remaining items
        selected_two_door_indices = self.knapsack_item_sorting(remaining_weights, remaining_bills, self.max_weight_two_door, len(remaining_items)) # Find the items selected for two door truck
        two_door_truck_items = [remaining_items[i] for i in selected_two_door_indices] # Create list of items for two door truck

        # Items that are not allocated to any truck and will be scheduled for the next delivery (if any)
        scheduled_for_next_delivery = [item for item in remaining_items if item not in two_door_truck_items and item not in one_door_truck_items]

        return one_door_truck_items, two_door_truck_items, oversized_items, scheduled_for_next_delivery

    # Display the results of the allocation
    def display_results(self):
        one_door_items, two_door_items, oversized_items, scheduled_for_next_delivery = self.allocate_items()

        # DataFrame from pandas to display table
        truck_results = {
            "One-Door Truck": pd.DataFrame(one_door_items),
            "Two-Door Truck": pd.DataFrame(two_door_items),
            "Oversized Items": pd.DataFrame(oversized_items),
            "Next Delivery": pd.DataFrame(scheduled_for_next_delivery),
            "Invalid Items": pd.DataFrame(self.invalid_items)
        }

        # Display truck results in a tabular format
        for truck_name, truck_df in truck_results.items():
            print(f"\n{truck_name}")
            if truck_df.empty:
                print(f"No items for {truck_name.lower()}.")
            else:
                # Format the DataFrame for better display
                if 'bill' in truck_df.columns:
                    truck_df['bill'] = truck_df['bill'].apply(lambda x: f"{x:,.0f} VND")
                print(tabulate(truck_df, headers='keys', tablefmt='grid', showindex=range(1, len(truck_df) + 1), maxcolwidths=20))

# Function to load items from a CSV file
def load_items_from_csv(file_path, destinations):
    try:
        df = pd.read_csv(file_path) # Read the CSV file
        items = []
        for _, row in df.iterrows():
            items.append({
                "name": row['name'],
                "price": row['price'],
                "weight": row['weight'],
                "height": row['height'],
                "length": row['length'],
                "width": row['width'],
                "city": row['city']
            })
        return items
    except FileNotFoundError: # Handle file not found error
        print(f"Error: The file '{file_path}' was not found.")
        return None
    except pd.errors.EmptyDataError: # Handle empty file error
        print(f"Error: The file '{file_path}' is empty or invalid.")
        return None
    except Exception: # Handle other exceptions
        print("Error: Unable to load the file. Please check the file format and try again.")
        return None

if __name__ == "__main__":
    destinations = {
        "HCMC": 1700,
        "Da Nang": 800,
        "Dalat": 1500,
        "Nha Trang": 1300,
        "Hai Phong": 100
    }

    while True:
        file_path = input("Enter the CSV file path (or type 'done' to exit): ").strip()
        if file_path.lower() == "done":
            print("Goodbye.")
            exit()  # Exit the program
        items_detail = load_items_from_csv(file_path, destinations)
        if items_detail is not None:  # If items were successfully loaded
            break
        print("Please try again with a valid file path.")

    allocator = TruckItemAllocator(
        max_weight_two_door=150,
        max_weight_one_door=100,
        weight_rate=500,
        distance_rate=200,
        destinations=destinations,
        items_detail=items_detail
    )

    allocator.display_results()
