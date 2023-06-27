from helpers.network_utils import NetworkElement

#works as both edge and relay, the only difference between them
#is how they behave in the tipology
if __name__ == '__main__':
    element = NetworkElement()
    element.run_network_element()