//
//  GatewayState.swift
//  5G-Check
//
//  Created by Steve Wiley on 11/4/22.
//

import Foundation

class GatewayState: ObservableObject {
    @Published var state = "?"
    @Published var rsrp = ChartData(name: "rsrp")
    @Published var signal = ChartData(name: "signal")
    @Published var connectionType = ChartData(name: "connection")
    @Published var token = ""
    @Published var isShowingStatistics = true
    @Published var duration = Duration.seconds(0)
    let startedAt = ContinuousClock.now
    
    init(asPreview: Bool) {
        if asPreview {
            self.rsrp = ChartData.example0()
            self.signal = ChartData.example1()
        }
    }
    
    static let numberFormatter: NumberFormatter = {
        let ret = NumberFormatter()
        ret.numberStyle = .decimal
        ret.usesGroupingSeparator = true
        ret.groupingSeparator = ","
        ret.groupingSize = 3
        return ret
    }()
    
    func update() {
        duration = ContinuousClock.now - startedAt
        if token.hasPrefix("sysauth=") {
            token = self.addDataPoints(authToken: token)
        }
    }
    
    func addDataPoints(authToken: String) -> String {
        var ret: String = authToken
        let url = URL(string: "http://192.168.0.1/cgi-bin/luci/verizon/network/getStatus")
        guard let requestUrl = url else { fatalError()}
        var request = URLRequest(url: requestUrl)
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        request.setValue(authToken, forHTTPHeaderField: "Cookie")
        request.httpMethod = "GET"
        let task = URLSession.shared.dataTask(with: request) { (data, response, error) in
            if let error = error {
                print("Error: \(error)")
                return
            }
            if let response = response as? HTTPURLResponse {
                print("Response HTTP Status code: \(response.statusCode)")
                if let newCookieHeader = response.value(forHTTPHeaderField: "Set-Cookie") {
                    let headerBits = newCookieHeader.components(separatedBy: ";")
                    ret = headerBits[0]
                }
                
            }
            if let data = data, let datastring = String(data: data, encoding: .utf8) {
                print("Response data string: \n \(datastring)")
            }
            do {
                if let results = try JSONSerialization.jsonObject(with: data!, options: []) as? NSDictionary {
                    if let newModemType = results["modemtype"] {
                        if let rsrpAsAny = results["rsrp"] {
                            if let signalAsAny = results["signal"] {
                                if let rsrpAsString = GatewayState.numberFormatter.string(for: Int(String(describing: rsrpAsAny))) {
                                    if let signalAsString = GatewayState.numberFormatter.string(for: Int(String(describing: signalAsAny))) {
                                        DispatchQueue.main.async {
                                            self.state = String(describing: newModemType)
                                            self.rsrp.incrementValue(withKey: rsrpAsString)
                                            self.signal.incrementValue(withKey: signalAsString)
                                            self.connectionType.incrementValue(withKey: String(describing: newModemType))
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            } catch let error as NSError {
                print(error.localizedDescription)
            }
        }
        task.resume()
        return ret
    }
}
