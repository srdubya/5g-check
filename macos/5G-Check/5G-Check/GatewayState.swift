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
    @Published var elapsed = ""
    let durationStyle = Duration.TimeFormatStyle(pattern: .hourMinuteSecond(padHourToLength: 2))
    var duration = Duration.seconds(0)
    var startedAt = ContinuousClock.now

    init(asPreview: Bool) {
        if asPreview {
            rsrp = ChartData.example0()
            signal = ChartData.example1()
        } else {
            if CommandLine.argc > 1 {
                self.token = CommandLine.arguments[1]
            }
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
        elapsed = duration.formatted(self.durationStyle)
        if token.hasPrefix("sysauth=") {
            token = addDataPoints(authToken: token)
        }
    }

    func clear() {
        DispatchQueue.main.async {
            self.state = "?"
            self.rsrp.clear()
            self.signal.clear()
            self.connectionType.clear()
            self.startedAt = ContinuousClock.now
        }
    }

    func addDataPoints(authToken: String) -> String {
        var ret: String = authToken
        let url = URL(string: "http://192.168.0.1/cgi-bin/luci/verizon/network/getStatus")
        guard let requestUrl = url else { fatalError() }
        var request = URLRequest(url: requestUrl)
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        request.setValue(authToken, forHTTPHeaderField: "Cookie")
        request.httpMethod = "GET"
        let task = URLSession.shared.dataTask(with: request) { data, response, error in
            if let error = error {
                print("Error: \(error)")
                DispatchQueue.main.async {
                    self.state = "??"
                }
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
                                if let rsrpAsString = GatewayState.numberFormatter.string(
                                    for: Int(String(describing: rsrpAsAny)))
                                {
                                    if let signalAsString = GatewayState.numberFormatter.string(
                                        for: Int(String(describing: signalAsAny)))
                                    {
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
                DispatchQueue.main.async {
                    self.state = "??"
                }
            }
        }
        task.resume()
        return ret
    }
}
