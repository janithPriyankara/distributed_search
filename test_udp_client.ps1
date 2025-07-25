# PowerShell UDP client script
param(
    [string]$Message = "Hello from PowerShell UDP client!",
    [string]$Server = "127.0.0.1",
    [int]$Port = 9000
)

try {
    # Create UDP client
    $udpClient = New-Object System.Net.Sockets.UdpClient
    
    # Convert message to bytes
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($Message)
    
    # Send message
    Write-Host "Sending message to $Server`:$Port"
    Write-Host "Message: $Message"
    
    $result = $udpClient.Send($bytes, $bytes.Length, $Server, $Port)
    
    Write-Host "✅ Sent $result bytes successfully!"
    
    # Close client
    $udpClient.Close()
    
    Write-Host "🎉 UDP test completed successfully!"
    Write-Host "Check the main application console for received message."
    
} catch {
    Write-Host "❌ Error sending UDP message: $($_.Exception.Message)" -ForegroundColor Red
} finally {
    if ($udpClient) {
        $udpClient.Dispose()
    }
}
