//
//  _G_CheckApp.swift
//  5G-Check
//
//  Created by Steve Wiley on 10/29/22.
//

import SwiftUI

class GatewayState: ObservableObject {
    @Published var state = "?"
    @Published var rsrp = ChartData(name: "rsrp")
    @Published var signal = ChartData(name: "signal")
    @Published var connectionType = ChartData(name: "connection")
    @Published var token = ""
    @Published var isShowingStatistics = true
    
    static let numberFormatter: NumberFormatter = {
        let ret = NumberFormatter()
        ret.numberStyle = .decimal
        ret.usesGroupingSeparator = true
        ret.groupingSeparator = ","
        ret.groupingSize = 3
        return ret
    }()
    
    func update() {
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

@main
struct CheckApp: App {
    @StateObject var carrierState = GatewayState()
    let timer = Timer.publish(every: 5, on: .main, in: .common).autoconnect()
    
    var body: some Scene {
        WindowGroup("StatisticWindow", id: "StatisticsWindow") {
            ContentView()
                .frame(minWidth: 300, idealWidth: 400, minHeight: 200, idealHeight: 300)
                .environmentObject(carrierState)
                .onDisappear(perform: {
                    carrierState.isShowingStatistics = false
                })
//                .onReceive(timer, perform: { _ in
//                    carrierState.update()
//                })
        }
        .handlesExternalEvents(matching: ["StatisticsWindow"])
        
        MenuBarExtra(content: {
            Button("Statistics..."){
                carrierState.isShowingStatistics = true
                OpenWindows.MainWindow.open()
            }.disabled(carrierState.isShowingStatistics)
            Button("Quit") {
                NSApplication.shared.terminate(nil)
            }
        } , label: {
            Text(carrierState.state).onReceive(timer, perform: { _ in
                carrierState.update()
            })
        })
    }
}

enum OpenWindows: String, CaseIterable {
    case MainWindow = "StatisticsWindow"
    
    func open() {
        if let url = URL(string: "StatisticsWindow://\(self.rawValue)") {
            NSWorkspace.shared.open(url)
        }
    }
}
