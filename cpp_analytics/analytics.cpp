#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <map>
#include <algorithm>
#include <iomanip>
#include <cmath>

using namespace std;

struct Sale {
    int id;
    double total;
    string date;
};

// Парсинг JSON (спрощений)
vector<Sale> parseSales(const string& json) {
    vector<Sale> sales;
    size_t pos = json.find("\"sales\"");
    if (pos == string::npos) return sales;
    
    pos = json.find("[", pos);
    if (pos == string::npos) return sales;
    
    while (true) {
        pos = json.find("{", pos);
        if (pos == string::npos) break;
        
        Sale sale;
        
        // Парсинг id
        size_t idPos = json.find("\"id\"", pos);
        if (idPos != string::npos) {
            idPos = json.find(":", idPos);
            sale.id = stoi(json.substr(idPos + 1));
        }
        
        // Парсинг total
        size_t totalPos = json.find("\"total\"", pos);
        if (totalPos != string::npos) {
            totalPos = json.find(":", totalPos);
            sale.total = stod(json.substr(totalPos + 1));
        }
        
        // Парсинг date
        size_t datePos = json.find("\"date\"", pos);
        if (datePos != string::npos) {
            datePos = json.find("\"", datePos + 6);
            size_t dateEnd = json.find("\"", datePos + 1);
            sale.date = json.substr(datePos + 1, dateEnd - datePos - 1);
        }
        
        sales.push_back(sale);
        pos = json.find("}", pos);
        if (pos == string::npos) break;
        pos++;
    }
    
    return sales;
}

// Топ товарів за виручкою (симуляція)
map<string, double> calculateTopProducts(const vector<Sale>& sales) {
    map<string, double> productTotals;
    
    // Симуляція розподілу продажів по товарах
    vector<string> products = {"Товар A", "Товар B", "Товар C", "Товар D", "Товар E"};
    
    for (const auto& sale : sales) {
        // Розподіл суми продажу між товарами
        int productIndex = sale.id % products.size();
        productTotals[products[productIndex]] += sale.total / (products.size() - productIndex + 1);
    }
    
    return productTotals;
}

// Агрегація виручки по днях
map<string, double> aggregateByDate(const vector<Sale>& sales) {
    map<string, double> dailyTotals;
    
    for (const auto& sale : sales) {
        dailyTotals[sale.date] += sale.total;
    }
    
    return dailyTotals;
}

// Вивід JSON
void outputJSON(const map<string, double>& data, const string& keyName) {
    cout << "{\"" << keyName << "\":[";
    bool first = true;
    for (const auto& pair : data) {
        if (!first) cout << ",";
        cout << "{\"name\":\"" << pair.first << "\",\"value\":" << fixed << setprecision(2) << pair.second << "}";
        first = false;
    }
    cout << "]}";
}

int main() {
    // Читання JSON з stdin
    string input;
    string line;
    while (getline(cin, line)) {
        input += line;
    }
    
    if (input.empty()) {
        cout << "{\"error\":\"No input data\"}";
        return 1;
    }
    
    // Парсинг продажів
    vector<Sale> sales = parseSales(input);
    
    if (sales.empty()) {
        cout << "{\"error\":\"No sales found\"}";
        return 1;
    }
    
    // Обчислення аналітики
    map<string, double> topProducts = calculateTopProducts(sales);
    map<string, double> dailyRevenue = aggregateByDate(sales);
    
    // Вивід результату
    cout << "{";
    cout << "\"top_products\":[";
    bool first = true;
    for (const auto& pair : topProducts) {
        if (!first) cout << ",";
        cout << "{\"name\":\"" << pair.first << "\",\"revenue\":" << fixed << setprecision(2) << pair.second << "}";
        first = false;
    }
    cout << "],";
    
    cout << "\"daily_revenue\":[";
    first = true;
    for (const auto& pair : dailyRevenue) {
        if (!first) cout << ",";
        cout << "{\"date\":\"" << pair.first << "\",\"total\":" << fixed << setprecision(2) << pair.second << "}";
        first = false;
    }
    cout << "],";
    
    // Загальна статистика
    double totalRevenue = 0;
    for (const auto& sale : sales) {
        totalRevenue += sale.total;
    }
    
    cout << "\"statistics\":{";
    cout << "\"total_revenue\":" << fixed << setprecision(2) << totalRevenue << ",";
    cout << "\"total_sales\":" << sales.size() << ",";
    cout << "\"average_sale\":" << fixed << setprecision(2) << (sales.empty() ? 0 : totalRevenue / sales.size());
    cout << "}";
    cout << "}";
    
    return 0;
}

